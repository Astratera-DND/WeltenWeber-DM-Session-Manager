"""Download portable VLC (win64) and copy libvlc.dll, libvlccore.dll and plugins/ into vlc_bundle/.
Used by the GitHub workflow and by build_windows.bat. Prints what it does so failures are easy to read."""
import os, shutil, sys, urllib.request, zipfile

VERSION = "3.0.21"
URLS = [
    f"https://get.videolan.org/vlc/{VERSION}/win64/vlc-{VERSION}-win64.zip",
    f"https://download.videolan.org/pub/videolan/vlc/{VERSION}/win64/vlc-{VERSION}-win64.zip",
    f"https://ftp.fau.de/videolan/vlc/{VERSION}/win64/vlc-{VERSION}-win64.zip",
    f"https://mirror.netcologne.de/videolan.org/vlc/{VERSION}/win64/vlc-{VERSION}-win64.zip",
]
ZIP, EXTRACT, BUNDLE = "vlc.zip", "vlc_extract", "vlc_bundle"

def download():
    for url in URLS:
        try:
            print("Downloading", url, flush=True)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r, open(ZIP, "wb") as f:
                shutil.copyfileobj(r, f)
            size = os.path.getsize(ZIP)
            print("  got", size, "bytes", flush=True)
            if size > 10_000_000 and zipfile.is_zipfile(ZIP):
                return True
            print("  not a valid VLC zip, trying next mirror")
        except Exception as e:
            print("  failed:", repr(e), flush=True)
    return False

def main():
    if not download():
        sys.exit("ERROR: could not download VLC from any mirror")
    shutil.rmtree(EXTRACT, ignore_errors=True)
    shutil.rmtree(BUNDLE, ignore_errors=True)
    with zipfile.ZipFile(ZIP) as z:
        z.extractall(EXTRACT)
    src = None
    for dp, dn, fn in os.walk(EXTRACT):
        if "libvlc.dll" in fn:
            src = dp
            break
    if not src:
        sys.exit("ERROR: libvlc.dll not found in the downloaded archive")
    print("VLC folder:", src)
    os.makedirs(BUNDLE)
    for name in ("libvlc.dll", "libvlccore.dll"):
        shutil.copy2(os.path.join(src, name), BUNDLE)
    shutil.copytree(os.path.join(src, "plugins"), os.path.join(BUNDLE, "plugins"))
    print("OK: vlc_bundle ready,", sum(len(f) for _, _, f in os.walk(BUNDLE)), "files")

if __name__ == "__main__":
    main()
