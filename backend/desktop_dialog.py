"""Native Windows dialogs for the packaged app, with no GUI runtime to bundle."""

import ctypes as ct
import logging
import struct
from ctypes import wintypes as wt


_DIALOG_PROCEDURE = ct.WINFUNCTYPE(ct.c_ssize_t, wt.HWND, wt.UINT, ct.c_size_t, ct.c_ssize_t)
_BUTTON = 0x0080
_STATIC = 0x0082
_CANCEL = 2
_CHILD_VISIBLE = 0x50000000
_TAB_STOP = 0x00010000


def _wide_text(text):
    return text.encode("utf-16-le") + b"\0\0"


def _dialog_template(title, heading, body, choices, default):
    width = 288
    body_height = 11 * (body.count("\n") + 2)
    button_top = 28 + body_height
    height = button_top + 27
    # WS_POPUP | WS_CAPTION | WS_SYSMENU | DS_CENTER | DS_MODALFRAME | DS_SETFONT
    style = 0x80C808C0
    template = bytearray(struct.pack("<IIHhhhh", style, 0, len(choices) + 2, 0, 0, width, height))
    template.extend(b"\0\0\0\0" + _wide_text(title))  # No menu, built-in dialog class.
    template.extend(struct.pack("<H", 9) + _wide_text("Microsoft YaHei UI"))

    def append_control(control_class, control_id, text, x, y, w, h, control_style=0):
        # Each item template begins at a DWORD boundary.
        template.extend(b"\0" * (-len(template) % 4))
        template.extend(struct.pack("<IIhhhhH", _CHILD_VISIBLE | control_style, 0, x, y, w, h, control_id))
        template.extend(struct.pack("<HH", 0xFFFF, control_class) + _wide_text(text) + b"\0\0")

    append_control(_STATIC, 0xFFFF, heading, 12, 10, width - 24, 12)
    append_control(_STATIC, 0xFFFF, body, 12, 26, width - 24, body_height)
    button_width = 73
    first_x = width - 12 - (button_width + 7) * len(choices) + 7
    for index, (button_id, label) in enumerate(choices):
        button_style = _TAB_STOP | int(button_id == default)  # BS_DEFPUSHBUTTON is 1.
        append_control(_BUTTON, button_id, label, first_x + index * (button_width + 7), button_top,
                       button_width, 16, button_style)
    return ct.create_string_buffer(bytes(template))


def dialog(title, heading, body, choices, *, default, on_click=None):
    """Show the launcher with custom buttons and return the selected button ID."""
    user32 = ct.WinDLL("user32", use_last_error=True)
    kernel32 = ct.WinDLL("kernel32", use_last_error=True)
    kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wt.HMODULE
    user32.EndDialog.argtypes = [wt.HWND, ct.c_ssize_t]
    user32.EndDialog.restype = wt.BOOL
    user32.DialogBoxIndirectParamW.argtypes = [wt.HINSTANCE, ct.c_void_p, wt.HWND, _DIALOG_PROCEDURE, ct.c_ssize_t]
    user32.DialogBoxIndirectParamW.restype = ct.c_ssize_t

    button_ids = {button_id for button_id, _ in choices}

    @_DIALOG_PROCEDURE
    def handle_message(window, message, w_param, _l_param):
        if message == 0x0110:  # WM_INITDIALOG
            logging.info("Opened launcher dialog: %s", heading)
            return 1
        if message == 0x0010:  # WM_CLOSE
            user32.EndDialog(window, _CANCEL)
            return 1
        if message == 0x0111:  # WM_COMMAND
            button_id = w_param & 0xFFFF
            if button_id not in button_ids:
                return 0
            if not on_click or not on_click(button_id):
                user32.EndDialog(window, button_id)
            return 1
        return 0

    template = _dialog_template(title, heading, body, choices, default)
    result = user32.DialogBoxIndirectParamW(kernel32.GetModuleHandleW(None), template, None, handle_message, 0)
    if result <= 0:
        raise ct.WinError(ct.get_last_error())
    return result


def notice(title, message, *, error=False):
    message_box = ct.WinDLL("user32").MessageBoxW
    message_box.argtypes = [wt.HWND, wt.LPCWSTR, wt.LPCWSTR, wt.UINT]
    message_box.restype = ct.c_int
    message_box(None, message, title, 0x10 if error else 0x40)
