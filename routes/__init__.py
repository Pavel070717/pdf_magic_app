"""
Routes package — registers all blueprints on a Flask app.
"""

from flask import Flask


def register_blueprints(app: Flask):
    from routes.aocr import aocr_bp
    from routes.converter import converter_bp
    from routes.dashboard import dashboard_bp
    from routes.directories import dir_bp
    from routes.files import files_bp
    from routes.magic import magic_bp
    from routes.materials import materials_bp
    from routes.registry import registry_bp
    from routes.requisites import requisites_bp
    from routes.rules import rules_bp
    from routes.state import state_bp

    app.register_blueprint(aocr_bp)
    app.register_blueprint(converter_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(registry_bp)
    app.register_blueprint(magic_bp)
    app.register_blueprint(dir_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(state_bp)
    app.register_blueprint(requisites_bp)
