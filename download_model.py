
import os
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    # Try to set encoding to utf-8, fallback to ignoring errors if that fails
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        else:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
    except Exception:
        pass  # If all else fails, let it be

print("🚀 Starting explicit model download...")
print("📦 Model: intfloat/multilingual-e5-large")

try:
    from huggingface_hub import snapshot_download
    
    # Download with progress bar
    print("\n⏳ Downloading model files (this may take a while)...")
    local_dir = snapshot_download(
        repo_id="intfloat/multilingual-e5-large",
        library_name="sentence-transformers",
        ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*.tflite", "*.onnx"],  # Ignore unnecessary formats to save bandwidth
        local_files_only=False
    )
    
    print(f"\n✅ Download complete!")
    print(f"📂 Model stored at: {local_dir}")
    print("\nYou can now restart the application.")

except ImportError:
    print("❌ Error: huggingface_hub not installed.")
    print("Please run: pip install huggingface_hub")
except Exception as e:
    print(f"\n❌ Download failed: {str(e)}")
    import traceback
    traceback.print_exc()
