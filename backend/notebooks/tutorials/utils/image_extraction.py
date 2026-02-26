# Full ChatGPT generated, just for example in 2a_doc_parsing.ipynb

import io
import numpy as np
from PIL import Image, UnidentifiedImageError


def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _colorspace_ncomp(cs):
    """
    Return number of components for common PDF colorspaces.
    Handles /DeviceRGB, /DeviceGray, /DeviceCMYK and simple /ICCBased.
    """
    try:
        name = str(cs)

        if name.endswith("DeviceRGB"):
            return 3
        if name.endswith("DeviceGray"):
            return 1
        if name.endswith("DeviceCMYK"):
            return 4

        # ICCBased: ["/ICCBased", icc_stream]
        if (
            isinstance(cs, (list, tuple))
            and len(cs) >= 2
            and str(cs[0]).endswith("ICCBased")
        ):
            icc = cs[1].get_object()
            n = icc.get("/N")
            if n:
                return int(n)

    except Exception:
        pass

    return None


def pdf_xobj_to_pil_image(xobj, page_num=None, idx=None, save_fallback=False):
    """
    Convert a pypdf image XObject to a PIL Image.

    Parameters
    ----------
    xobj : pypdf generic object
        The image XObject.
    page_num : int, optional
        Only used for debug messages.
    idx : int, optional
        Only used for debug messages.
    save_fallback : bool
        If True, dumps raw JPEG/JP2 stream when PIL can't decode.

    Returns
    -------
    PIL.Image or None
    """

    try:
        # Skip soft masks (can be handled separately if desired)
        if xobj.get("/SMask"):
            return None

        filters = [str(f) for f in _as_list(xobj.get("/Filter"))]
        data = xobj.get_data()

        # -------------------------------------------------
        # FAST PATH → JPEG / JPEG2000
        # -------------------------------------------------
        if any("DCTDecode" in f for f in filters) or any(
            "JPXDecode" in f for f in filters
        ):
            try:
                img = Image.open(io.BytesIO(data))
                img.load()
                return img

            except UnidentifiedImageError:
                if save_fallback:
                    ext = "jpg" if any("DCTDecode" in f for f in filters) else "jp2"
                    out = f"page_{page_num}_img_{idx}.{ext}"
                    with open(out, "wb") as f:
                        f.write(data)
                    print(
                        f"[page {page_num}] PIL couldn't decode; wrote raw stream to {out}"
                    )
                return None

        # -------------------------------------------------
        # RAW PIXEL PATH (FlateDecode etc.)
        # -------------------------------------------------
        w = int(xobj["/Width"])
        h = int(xobj["/Height"])
        bpc = int(xobj.get("/BitsPerComponent", 8))
        cs = xobj.get("/ColorSpace", "/DeviceRGB")
        ncomp = _colorspace_ncomp(cs)

        if bpc != 8:
            print(f"[page {page_num}] Unsupported BitsPerComponent={bpc}")
            return None

        if ncomp not in (1, 3, 4):
            print(f"[page {page_num}] Unknown ColorSpace={cs}")
            return None

        expected = w * h * ncomp
        if len(data) < expected:
            print(f"[page {page_num}] Not enough bytes ({len(data)} < {expected})")
            return None

        if len(data) > expected:
            data = data[:expected]

        arr = np.frombuffer(data, dtype=np.uint8).reshape((h, w, ncomp))

        if ncomp == 1:
            return Image.fromarray(arr[:, :, 0], mode="L")
        elif ncomp == 3:
            return Image.fromarray(arr, mode="RGB")
        else:  # CMYK
            return Image.fromarray(arr, mode="CMYK").convert("RGB")

    except Exception as e:
        print(f"[page {page_num}] Failed to decode image {idx}: {e}")
        return None
