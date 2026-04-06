# python/routes/authentication.py


from flask import Blueprint, flash, redirect, render_template, request, session, url_for,jsonify

from python.models import db
from python.models.modelos import *
from python.services.system.email import *
from functools import wraps 
import secrets
import string
from sqlalchemy import or_,and_,cast, String,func,text
from datetime import date, timedelta
import re
from python.services.system.extensions import csrf,limiter
from python.services.system.helper_functions import *
from python.services.system.template_formats import *
from webauthn.helpers import options_to_json, base64url_to_bytes,bytes_to_base64url
import os
from config import *

from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    AuthenticatorAttestationResponse,
    PublicKeyCredentialDescriptor,
    AuthenticationCredential,
    AuthenticatorAssertionResponse    
)
from webauthn import (
    generate_registration_options,
    generate_authentication_options,
    verify_registration_response,
    verify_authentication_response,
    
)
from webauthn.helpers.exceptions import (
    InvalidRegistrationResponse,
    InvalidAuthenticationResponse
)
import base64
from dotenv import load_dotenv
load_dotenv()

RP_NAME = os.getenv('RP_NAME')
ORIGIN=os.getenv('ORIGIN')
RP_ID=os.getenv('RP_ID')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id_usuario' not in session:
            return redirect(url_for('auth.login', next=request.url))
        else:
            usuario = Usuarios.query.get(session['id_usuario'])
            if not usuario or usuario.estatus == 'Inactivo':
                session.clear()
                flash("Tu cuenta se encuentra Inactiva. Favor de revisar con tu administrador.", "info")
                return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def routes_accessible_by_user(id_user, id_role):
    """
    Preload all routes the user and their role have access to.
    """
    query = """
    SELECT DISTINCT r.ruta
    FROM rutas r
    LEFT JOIN relacion_rutas_roles ro ON r.id = ro.id_ruta AND ro.id_rol = :id_rol
    WHERE ro.id_rol IS NOT NULL
    """
    result = db.session.execute(text(query), {'id_usuario': id_user, 'id_rol': id_role}).fetchall()
    session['accessible_routes'] = {row[0] for row in result} 

def access_control(path):
    """
    Check if the current user has access to the given path using cached routes.
    """
    id_user = session.get('id_usuario')
    id_role = session.get('id_rol')
    accessible_routes = session.get('accessible_routes')

    if not id_user or not id_role or not accessible_routes:
        return False

    if path in accessible_routes:
        return True
    # Check parent paths
    while path:
        path = path.rsplit('/', 1)[0]  # Remove the last segment
        if path in accessible_routes:
            return True
    # Check root route
    return '/' in accessible_routes

def roles_required():
    def decorator(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            path = request.path
            if not access_control(path):
                flash("No tienes permiso para acceder al módulo/funcionalidad seleccionada.", "danger")
                return redirect(request.referrer or '/')
            return func(*args, **kwargs)
        return wrapped_function
    return decorator

auth_bp = Blueprint("auth", __name__, url_prefix="/authentication")

@auth_bp.route("/login")
def login():
    return render_template("system/authentication/login.html")

@auth_bp.route("/signin")
def signin():
    return render_template("system/authentication/signin.html")

@auth_bp.route('/login_submit', methods=['POST'])
@limiter.limit("5 per minute")
def login_submit():
    correo_electronico = request.form['correo_electronico']
    contrasena = request.form['contrasena']
    usuario = Usuarios.query.filter(Usuarios.correo_electronico==correo_electronico).first()
    if usuario!=None:
        if (usuario.estatus=='Activo') or usuario.rol.nombre == 'Sistema':
            # revisar ultimo cambio de contrasena
            if (date.today() - usuario.ultimo_cambio_de_contrasena) >= timedelta(days=365):
                flash("Tu contraseña no ha cambiado en mucho tiempo. Favor de cambiar tu contraseña.", "info")
                return redirect(url_for("auth.login"))
            # revisar # de intentento de sesion
            if usuario.intentos_de_inicio_de_sesion>3:
                flash("Has intentando inciar sesión en varias ocaciones sin éxito. Favor de cambiar tu contraseña.", "info")
                return redirect(url_for("auth.login"))
            if check_password_hash(usuario.contrasena, contrasena) or (contrasena==usuario.codigo_unico_login and usuario.codigo_unico_expira > datetime.now()):
                session.clear()
                stmt = db.select(roles_aplicaciones.c.id_aplicacion).where(roles_aplicaciones.c.id_rol == usuario.id_rol)
                result = db.session.execute(stmt).fetchall()
                lista_ids = [row[0] for row in result]
                aplicaciones_obj = Aplicaciones.query.filter(Aplicaciones.id.in_(lista_ids)).all()                 
                session['id_usuario'] = usuario.id
                session['nombre'] = usuario.nombre
                session['correo'] = usuario.correo_electronico
                session['aplicaciones'] = [a.nombre for a in aplicaciones_obj]
                session['aplicacion'] = session['aplicaciones'][0] if session['aplicaciones'] else None
                session['id_rol'] = usuario.id_rol
                session['nombre_rol'] = usuario.rol.nombre
                session['tabla_origen']=''
                # Obtener y almacenar rol en sesion
                routes_accessible_by_user(session['id_usuario'], session['id_rol'])
                session['table_names'] = sorted([model.__tablename__ for model in get_all_models() if can_access(f'/dynamic/{model.__tablename__}/view') and model.__tablename__ not in OMIT_TABLES])
                usuario.ultima_sesion=datetime.now()
                usuario.intentos_de_inicio_de_sesion=0
                db.session.commit()
                flash(f"¡Bienvenido, {usuario.nombre}!", "success")
                return redirect(url_for("home.home"))
            else:
                usuario.intentos_de_inicio_de_sesion=usuario.intentos_de_inicio_de_sesion+1
                db.session.commit()
                flash("Información incorrecta. Inténtalo nuevamente.", "info")
                return redirect(url_for("auth.login"))
        else:
            flash("Tu cuenta se encuentra Inactiva. Favor de revisar con tu administrador.", "info")
            return redirect(url_for("auth.login"))
    else:
        flash("Información incorrecta. Inténtalo nuevamente.", "info")
        return redirect(url_for("auth.login"))

@auth_bp.route("/forgotpassword")
def forgot_password():
    return render_template("system/authentication/forgotpassword.html")

@auth_bp.route('/forgotpassword_submit', methods=['POST'])
@limiter.limit("3 per minute")  # Stricter for password reset
def forgotpassword_submit():
    correo_electronico = request.form['correo_electronico']
    usuario = Usuarios.query.filter(Usuarios.correo_electronico==correo_electronico).first()
    if usuario!=None:
        usuario.codigo_unico = uuid.uuid4()
        usuario.codigo_unico_expira = datetime.now() + timedelta(minutes=15)
        forgot_password_email(correo_electronico,usuario.codigo_unico)
        usuario.intentos_de_inicio_de_sesion=0
        db.session.commit()
    flash("Si el correo electrónico ingresado esta registrado, recibirás las intrucciones para cambiar la contraseña.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route('/update_password/<unique_code>', methods=['GET'])
@limiter.limit("3 per minute")
def update_password(unique_code):
    user = Usuarios.query.filter(
        and_(
            Usuarios.codigo_unico == unique_code,
            Usuarios.codigo_unico_expira > datetime.now()
        )
    ).first()
    if user:
        return render_template("system/authentication/updatepassword.html",id_user=user.id)
    else:
        flash("El código no es válido.", "danger")
        return redirect(url_for('auth.login'))


def is_strong_password(password: str) -> bool:
    """Validate that a password is strong enough."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):  # uppercase
        return False
    if not re.search(r"[a-z]", password):  # lowercase
        return False
    if not re.search(r"[0-9]", password):  # digit
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>-]", password):  # special char
        return False
    return True

@auth_bp.route('/update_password_submit', methods=['POST'])
@limiter.limit("5 per minute")
def update_password_submit():
    data = {key: request.form.getlist(key) for key in request.form.keys()}
    password = data['password'][0]
    confirm_password = data['confirm_password'][0]

    try:
        user = Usuarios.query.get(uuid.UUID(data['id_user'][0]))
    except Exception:
        flash("El usuario no es válido.", "danger")
        return redirect(request.referrer or url_for('auth.login'))

    if not user:
        flash("Usuario no encontrado.", "danger")
        return redirect(request.referrer or url_for('auth.login'))

    if password != confirm_password:
        flash("Las contraseñas no son iguales. Favor de revisar.", "warning")
        return redirect(request.referrer or url_for('auth.login'))

    if not is_strong_password(password):
        flash("La contraseña no cumple los requisitos de seguridad: "
              "mínimo 8 caracteres, una mayúscula, una minúscula, un número y un caracter especial.", 
              "danger")
        return redirect(request.referrer or url_for('auth.login'))

    user.contrasena = generate_password_hash(password)
    user.codigo_unico = None
    user.codigo_unico_login = None
    db.session.commit()
    flash("La contraseña ha sido actualizada.", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route("/passkey/register/options", methods=["POST"])
@csrf.exempt
def passkey_register_options():
    user_id = session.get("id_usuario")
    user = Usuarios.query.get(user_id)
    if not user:
        return jsonify({"error": "User not logged in"}), 401

    

    options = generate_registration_options(
        rp_id = RP_ID,
        rp_name=RP_NAME,
        user_id=str(user.id).encode(),
        user_name=user.correo_electronico,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED
        ),
    )

    session["webauthn_challenge"] = bytes_to_base64url(options.challenge)
    return options_to_json(options)

@auth_bp.route("/passkey/register/verify", methods=["POST"])
@csrf.exempt
def passkey_register_verify():
    user_id = session.get("id_usuario")
    body = request.get_json()
    challenge = session.pop("webauthn_challenge", None)
    if not challenge:
        return jsonify({"error": "Missing challenge"}), 400

    try:
        # ✅ Build nested AuthenticatorAttestationResponse
        response_obj = AuthenticatorAttestationResponse(
            client_data_json=base64.b64decode(body["response"]["clientDataJSON"]),
            attestation_object=base64.b64decode(body["response"]["attestationObject"]),
        )

        credential = RegistrationCredential(
            id=body["id"],
            raw_id=base64.b64decode(body["raw_id"]),
            response=response_obj,
            type=body.get("type", "public-key"),
        )

        verification = verify_registration_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(challenge),
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
        )

    except InvalidRegistrationResponse as e:
        return jsonify({"error": f"Verification failed: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 400

    # ✅ If no error → verified
    cred = CredencialesDeUsuarios(
        id_usuario=user_id,
        id_credenciales=base64.b64encode(verification.credential_id).decode(),
        public_key=base64.b64encode(verification.credential_public_key).decode(),
        sign_count=verification.sign_count,
    )
    db.session.add(cred)
    db.session.commit()

    return jsonify({"status": "ok"})


@auth_bp.route("/passkey/login/options", methods=["POST"])
@csrf.exempt
def passkey_login_options():
    #correo_electronico = request.json["correo_electronico"]
    #user = Usuarios.query.filter_by(correo_electronico=correo_electronico).first()
    #if not user:
    #    return jsonify({"error": "User not found"}), 404

    credentials = CredencialesDeUsuarios.query.filter(Usuarios.estatus=="Activo").all()
    if not credentials:
        return jsonify({"error": "No passkey registered"}), 404

    # ✅ Build allowCredentials list
    allow_creds = [
        PublicKeyCredentialDescriptor(id=base64.b64decode(c.id_credenciales))
        for c in credentials
    ]

    # ✅ Generate WebAuthn options
    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_creds,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    # ✅ Store challenge in base64url for later comparison
    session["webauthn_challenge"] = bytes_to_base64url(options.challenge)
    #session["pending_login_user_id"] = user.id

    return options_to_json(options)


@auth_bp.route("/passkey/login/verify", methods=["POST"])
@csrf.exempt
def passkey_login_verify():
    body = request.get_json()
    challenge = session.pop("webauthn_challenge", None)

    if not challenge:
        return jsonify({"error": "Missing challenge or user"}), 400
    
    cred = CredencialesDeUsuarios.query.filter_by(id_credenciales=body['raw_id']).first()
    if not cred:
        return jsonify({"error": "No credential found"}), 404
    user=Usuarios.query.get(cred.id_usuario)
    if not user or user.estatus != "Activo":
        return jsonify({"error": "Userio Inactivo"}), 403
    try:
        resp = body["response"]
        for key in ["authenticator_data", "client_data_json", "signature", "user_handle"]:
            if key in resp and isinstance(resp[key], str):
                try:
                    resp[key] = base64.b64decode(resp[key])
                except Exception:
                    pass
        body["response"] = resp

        # Decode raw_id if needed
        if isinstance(body.get("raw_id"), str):
            try:
                body["raw_id"] = base64.b64decode(body["raw_id"])
            except Exception:
                pass
            
        credential = AuthenticationCredential(
            id=body["id"],
            raw_id=body["raw_id"],
            response=AuthenticatorAssertionResponse(
                client_data_json=resp["client_data_json"],
                authenticator_data=resp["authenticator_data"],
                signature=resp["signature"],
                user_handle=resp.get("user_handle"),
            ),
            type=body["type"],
        )

        public_key_bytes = (
            cred.public_key if isinstance(cred.public_key, (bytes, bytearray))
            else base64.b64decode(cred.public_key)
        )

        expected_challenge = (
            base64url_to_bytes(challenge)
            if isinstance(challenge, str)
            else challenge
        )

        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=expected_challenge,
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=public_key_bytes,
            credential_current_sign_count=cred.sign_count,
        )

        # ✅ Success
        cred.sign_count = verification.new_sign_count
        db.session.commit()

        session.clear()
        stmt = db.select(roles_aplicaciones.c.id_aplicacion).where(roles_aplicaciones.c.id_rol == user.id_rol)
        result = db.session.execute(stmt).fetchall()
        lista_ids = [row[0] for row in result]
        aplicaciones_obj = Aplicaciones.query.filter(Aplicaciones.id.in_(lista_ids)).all()
        session['id_usuario'] = user.id
        session['nombre'] = user.nombre
        session['correo'] = user.correo_electronico
        session['aplicaciones'] = [a.nombre for a in aplicaciones_obj]
        session['aplicacion'] = session['aplicaciones'][0] if session['aplicaciones'] else None
        session['id_rol'] = user.id_rol
        session['nombre_rol'] = user.rol.nombre
        session['tabla_origen']=''
        routes_accessible_by_user(session['id_usuario'], session['id_rol'])
        session['table_names'] = sorted([model.__tablename__ for model in get_all_models() if can_access(f'/dynamic/{model.__tablename__}/view') and model.__tablename__ not in OMIT_TABLES])
        user.ultima_sesion=datetime.now()
        user.intentos_de_inicio_de_sesion=0
        db.session.commit()        
        flash(f"¡Bienvenido, {user.nombre}!", "success")

        return jsonify({"status": "ok"})

    except InvalidAuthenticationResponse as e:
        print("❌ Invalid authentication:", e)
        return jsonify({"error": f"Invalid authentication: {str(e)}"}), 400
    except Exception as e:
        print("❌ Unexpected error:", e)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 400


@auth_bp.route("/one_time_code_login/<email>", methods=["POST","GET"])
def send_one_time_code(email):
    user = Usuarios.query.filter_by(correo_electronico=email).first()
    if not user:
        return jsonify({"error": "Usuario no existe"}), 401
    user.codigo_unico_login = generate_pin()
    user.codigo_unico_expira = datetime.now() + timedelta(minutes=15)
    one_time_code_email(email,user.codigo_unico_login)
    db.session.commit()
    flash('Se ha enviado un código a tu correo electrónico para iniciar sesión.','success')
    return redirect(url_for("auth.login"))
