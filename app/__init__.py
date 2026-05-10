from flask import Flask
from app.config import Config
from app.extensions import db, jwt, socketio, cors

def create_app():
    app= Flask(__name__)
    app.config.from_object(Config)
    
    allowed_origins = [
        "http://localhost:5173",
        "https://munch-run-frontend.vercel.app",
    ]
    
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    cors.init_app(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "https://munch-run-frontend.vercel.app"
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
    })
    
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.menu import menu_bp
    from app.routes.orders import orders_bp
    from app.routes.slot import slot_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(menu_bp, url_prefix='/api/menu')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(slot_bp, url_prefix='/api/slots')
    
    with app.app_context():
        from app import socket
    
    return app
    