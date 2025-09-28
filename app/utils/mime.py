from io import BytesIO

import magic


def check_file_type(file: BytesIO) -> str:
    """
    Check and validate file MIME type.

    Args:
        file: BytesIO object containing file data
        accepted_mimes: List of accepted MIME types

    Returns:
        str: Detected MIME type

    Raises:
        BaseHTTPException: If file type is not supported
    """

    file.seek(0)  # Reset the file pointer to the beginning

    # Initialize the magic MIME type detector
    mime_detector = magic.Magic(mime=True)

    # Detect MIME type from the buffer
    mime_type = mime_detector.from_buffer(file.read(2048))  # Read the first 2048 bytes

    file.seek(0)  # Reset the file pointer to the beginning
    return mime_type
