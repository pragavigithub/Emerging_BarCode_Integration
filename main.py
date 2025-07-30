from app import app

# Import routes to register endpoints
import routes

# Apply enhanced bin scanning fix on startup (optional)
try:
    from sap_bin_scanning_fix import apply_bin_scanning_fix
    apply_bin_scanning_fix()
    print("✅ Enhanced bin scanning functionality loaded")
except ImportError:
    print("⚠️ Enhanced bin scanning fix not found, using default implementation")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
