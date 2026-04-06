# python/routes/errors.py

from flask import Blueprint, render_template, flash

errors_bp = Blueprint("errors", __name__)


@errors_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template("system/error404.html"), 404


@errors_bp.app_errorhandler(500)
def internal_error(error):
    #flash("An unexpected error occurred. Please try again later.", "danger")
    return render_template("system/error500.html"), 500
