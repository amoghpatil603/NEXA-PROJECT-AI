import sys

content = open("backend/utils/document_parser.py").read()
content = content.replace(
"""            except ImportError:
                content = "Error: required pdf/ocr libraries not installed.\"""",
"""            except ImportError as e:
                raise ImportError(f"Required pdf/ocr libraries not installed: {e}")"""
)
content = content.replace(
"""            except ImportError:
                content = "Error: python-docx not installed.\"""",
"""            except ImportError as e:
                raise ImportError(f"python-docx not installed: {e}")"""
)
content = content.replace(
"""            except ImportError:
                content = "Error: required ocr libraries not installed.\"""",
"""            except ImportError as e:
                raise ImportError(f"Required ocr libraries not installed: {e}")"""
)
content = content.replace(
"""            except UnicodeDecodeError:
                content = "Binary or unsupported content format.\"""",
"""            except UnicodeDecodeError as e:
                raise ValueError(f"Binary or unsupported content format: {e}")"""
)
open("backend/utils/document_parser.py", "w").write(content)
