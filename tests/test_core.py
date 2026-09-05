"""
Tests for routes/core.py — sanitization, tree builders, subfolder creation.
"""

import shutil
from pathlib import Path

from routes.core import (
    build_tree_from_created,
    build_tree_from_fs,
    create_subfolders,
    sanitize_folder_name,
    sanitize_text,
    tree_from_subfolders,
    update_tree_paths,
)


# ─── sanitize_text ───────────────────────────────────────────────


class TestSanitizeText:
    def test_normal_text(self):
        assert sanitize_text("Hello World") == "Hello World"

    def test_none_returns_empty(self):
        assert sanitize_text(None) == ""

    def test_empty_string(self):
        assert sanitize_text("") == ""

    def test_non_string_returns_empty(self):
        assert sanitize_text(123) == ""
        assert sanitize_text([]) == ""

    def test_strips_html_tags(self):
        assert sanitize_text("<b>Hello</b>") == "Hello"

    def test_strips_nested_html(self):
        result = sanitize_text("<div><span class='x'>Text</span></div>")
        assert result == "Text"

    def test_strips_angle_brackets(self):
        # <b> looks like an HTML tag and gets stripped
        result = sanitize_text("a < b > c")
        assert "<" not in result
        assert ">" not in result

    def test_strips_script_tags(self):
        # Only tags are stripped, not content between them
        result = sanitize_text("<script>alert('x')</script>Safe")
        assert "<script>" not in result
        assert "</script>" not in result
        assert "Safe" in result

    def test_strips_nested_tags(self):
        result = sanitize_text("<p><a href='http://x'>link</a></p>")
        assert result == "link"

    def test_strips_html_comments(self):
        result = sanitize_text("<!-- comment -->visible")
        assert "visible" in result
        assert "comment" not in result

    def test_whitespace_only(self):
        assert sanitize_text("   ") == ""

    def test_preserves_inner_whitespace(self):
        assert sanitize_text("hello  world") == "hello  world"


# ─── sanitize_folder_name ────────────────────────────────────────


class TestSanitizeFolderName:
    def test_normal_name(self):
        assert sanitize_folder_name("MyFolder") == "MyFolder"

    def test_none_returns_default(self):
        assert sanitize_folder_name(None) == "unnamed_folder"

    def test_empty_returns_default(self):
        assert sanitize_folder_name("") == "unnamed_folder"

    def test_non_string_returns_default(self):
        assert sanitize_folder_name(42) == "unnamed_folder"

    def test_replaces_forbidden_chars(self):
        result = sanitize_folder_name('test/\\:*?"<>|file')
        assert "/" not in result
        assert "\\" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result

    def test_strips_leading_trailing_dots_and_spaces(self):
        assert sanitize_folder_name("...folder...") == "folder"
        assert sanitize_folder_name("  folder  ") == "folder"

    def test_only_dots_and_spaces_returns_default(self):
        assert sanitize_folder_name("...") == "unnamed_folder"

    def test_preserves_underscores(self):
        assert sanitize_folder_name("my_folder") == "my_folder"

    def test_preserves_cyrillic(self):
        assert sanitize_folder_name("МояПапка") == "МояПапка"

    def test_mixed_forbidden_and_valid(self):
        result = sanitize_folder_name("Doc: <test>")
        assert result == "Doc_ _test_"


# ─── create_subfolders ──────────────────────────────────────────


class TestCreateSubfolders:
    def test_creates_simple_folders(self, temp_dir):
        tree = [{"name": "folder1"}, {"name": "folder2"}]
        result = create_subfolders(temp_dir, tree)
        assert (temp_dir / "folder1").is_dir()
        assert (temp_dir / "folder2").is_dir()
        assert len(result["created"]) == 2
        assert result["errors"] == []

    def test_creates_nested_folders(self, temp_dir):
        tree = [{"name": "parent", "children": [{"name": "child"}]}]
        result = create_subfolders(temp_dir, tree)
        assert (temp_dir / "parent" / "child").is_dir()
        assert "parent" in result["created"]
        assert "parent/child" in result["created"]

    def test_deeply_nested(self, temp_dir):
        tree = [
            {
                "name": "a",
                "children": [
                    {
                        "name": "b",
                        "children": [
                            {"name": "c"}
                        ],
                    }
                ],
            }
        ]
        result = create_subfolders(temp_dir, tree)
        assert (temp_dir / "a" / "b" / "c").is_dir()
        assert "a/b/c" in result["created"]

    def test_empty_tree(self, temp_dir):
        result = create_subfolders(temp_dir, [])
        assert result == {"created": [], "errors": []}

    def test_sanitizes_names(self, temp_dir):
        tree = [{"name": "bad:name"}]
        result = create_subfolders(temp_dir, tree)
        assert len(result["created"]) == 1
        assert (temp_dir / "bad_name").is_dir()

    def test_existing_folder_no_error(self, temp_dir):
        (temp_dir / "exists").mkdir()
        tree = [{"name": "exists"}]
        result = create_subfolders(temp_dir, tree)
        assert result["errors"] == []
        assert (temp_dir / "exists").is_dir()

    def test_empty_name_becomes_unnamed(self, temp_dir):
        # sanitize_folder_name("") → "unnamed_folder", which IS created
        tree = [{"name": ""}, {"name": "   "}]
        result = create_subfolders(temp_dir, tree)
        assert len(result["created"]) == 2
        for name in result["created"]:
            assert name == "unnamed_folder"

    def test_multiple_siblings(self, temp_dir):
        tree = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        result = create_subfolders(temp_dir, tree)
        assert len(result["created"]) == 3


# ─── build_tree_from_fs ─────────────────────────────────────────


class TestBuildTreeFromFs:
    def test_empty_directory(self, temp_dir):
        assert build_tree_from_fs(temp_dir) == []

    def test_files_ignored(self, temp_dir):
        (temp_dir / "file.txt").touch()
        assert build_tree_from_fs(temp_dir) == []

    def test_subdirectories(self, temp_dir):
        (temp_dir / "folder1").mkdir()
        (temp_dir / "folder2").mkdir()
        tree = build_tree_from_fs(temp_dir)
        names = [n["name"] for n in tree]
        assert "folder1" in names
        assert "folder2" in names

    def test_nested_structure(self, temp_dir):
        (temp_dir / "a").mkdir()
        (temp_dir / "a" / "b").mkdir()
        tree = build_tree_from_fs(temp_dir)
        assert len(tree) == 1
        assert tree[0]["name"] == "a"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["name"] == "b"

    def test_sorted_output(self, temp_dir):
        (temp_dir / "z_folder").mkdir()
        (temp_dir / "a_folder").mkdir()
        (temp_dir / "m_folder").mkdir()
        tree = build_tree_from_fs(temp_dir)
        names = [n["name"] for n in tree]
        assert names == sorted(names)

    def test_nonexistent_directory(self):
        result = build_tree_from_fs(Path("/nonexistent/path/xyz"))
        assert result == []


# ─── tree_from_subfolders ───────────────────────────────────────


class TestTreeFromSubfolders:
    def test_empty(self):
        assert tree_from_subfolders([], "/base") == []

    def test_simple_nodes(self):
        nodes = [{"name": "a"}, {"name": "b"}]
        result = tree_from_subfolders(nodes, "/base")
        assert len(result) == 2
        assert result[0]["name"] == "a"
        assert str(Path("/base") / "a") in result[0]["path"]
        assert result[0]["type"] == "folder"

    def test_nested_nodes(self):
        nodes = [{"name": "a", "children": [{"name": "b"}]}]
        result = tree_from_subfolders(nodes, "/base")
        assert str(Path("/base") / "a" / "b") in result[0]["children"][0]["path"]

    def test_windows_paths(self):
        nodes = [{"name": "folder"}]
        result = tree_from_subfolders(nodes, "C:\\Users\\test")
        assert "C:" in result[0]["path"] or "folder" in result[0]["path"]


# ─── update_tree_paths ──────────────────────────────────────────


class TestUpdateTreePaths:
    def test_empty_tree(self):
        nodes = []
        update_tree_paths(nodes, "/old", "/new")
        assert nodes == []

    def test_updates_matching_paths(self):
        nodes = [{"name": "a", "path": "/old/sub/dir"}]
        update_tree_paths(nodes, "/old", "/new")
        assert nodes[0]["path"] == "/new/sub/dir"

    def test_ignores_non_matching_paths(self):
        nodes = [{"name": "a", "path": "/other/sub"}]
        update_tree_paths(nodes, "/old", "/new")
        assert nodes[0]["path"] == "/other/sub"

    def test_nested_paths_updated(self):
        nodes = [{"name": "a", "path": "/old/a", "children": [{"name": "b", "path": "/old/a/b"}]}]
        update_tree_paths(nodes, "/old", "/new")
        assert nodes[0]["children"][0]["path"] == "/new/a/b"

    def test_empty_path_unchanged(self):
        nodes = [{"name": "a", "path": ""}]
        update_tree_paths(nodes, "/old", "/new")
        assert nodes[0]["path"] == ""

    def test_no_path_key_unchanged(self):
        nodes = [{"name": "a"}]
        update_tree_paths(nodes, "/old", "/new")
        assert nodes[0].get("path") is None


# ─── build_tree_from_created ────────────────────────────────────


class TestBuildTreeFromCreated:
    def test_empty(self):
        assert build_tree_from_created([]) == []

    def test_groups_by_date(self):
        dirs = [
            {"date": "2026-01-15", "project_code": "A", "path": "/p/a"},
            {"date": "2026-01-15", "project_code": "B", "path": "/p/b"},
        ]
        tree = build_tree_from_created(dirs)
        assert len(tree) == 1
        assert tree[0]["name"] == "2026-01-15"
        assert len(tree[0]["children"]) == 2

    def test_dates_sorted_descending(self):
        dirs = [
            {"date": "2026-01-01", "project_code": "A", "path": "/a"},
            {"date": "2026-06-01", "project_code": "B", "path": "/b"},
            {"date": "2026-03-01", "project_code": "C", "path": "/c"},
        ]
        tree = build_tree_from_created(dirs)
        dates = [n["name"] for n in tree]
        assert dates == ["2026-06-01", "2026-03-01", "2026-01-01"]

    def test_projects_sorted_by_code(self):
        dirs = [
            {"date": "2026-01-01", "project_code": "Z", "path": "/z"},
            {"date": "2026-01-01", "project_code": "A", "path": "/a"},
        ]
        tree = build_tree_from_created(dirs)
        codes = [c["name"] for c in tree[0]["children"]]
        assert codes == ["A", "Z"]

    def test_empty_date_group_skipped(self):
        dirs = [{"date": "2026-01-01", "project_code": "", "path": ""}]
        tree = build_tree_from_created(dirs)
        assert len(tree) == 1

    def test_entry_type_is_date(self):
        dirs = [{"date": "2026-01-01", "project_code": "X", "path": "/x"}]
        tree = build_tree_from_created(dirs)
        assert tree[0]["type"] == "date"

    def test_project_type_is_project(self):
        dirs = [{"date": "2026-01-01", "project_code": "X", "path": "/x"}]
        tree = build_tree_from_created(dirs)
        assert tree[0]["children"][0]["type"] == "project"
