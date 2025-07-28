from app import app

# Apply enhanced bin scanning fix on startup
try:
    from sap_bin_scanning_fix import apply_bin_scanning_fix
    apply_bin_scanning_fix()
    print("✅ Enhanced bin scanning functionality loaded")
except ImportError:
    print("⚠️ Enhanced bin scanning fix not found, using default implementation")
import routes

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
