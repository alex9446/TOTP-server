import tkinter as tk
from base64 import b32encode
from secrets import token_bytes as random_bytes

from apscheduler.schedulers.background import BackgroundScheduler
from PIL.ImageTk import PhotoImage
from pyotp import TOTP
from qrcode import make as qr_make

SECRET_FILE = 'secret'
WINDOW_TITLE = 'OTP-Server'


# Create new base32 encoded secret, save in to a file and return it
def set_secret() -> str:
    secret = b32encode(random_bytes(20))
    with open(SECRET_FILE, 'wb') as f:
        f.write(secret)
    return secret


# Get base32 encoded secret from a file
# or generate new one if the file not exist
def get_secret() -> str:
    secret = None
    try:
        with open(SECRET_FILE, 'rb') as f:
            secret = f.read()
    except FileNotFoundError:
        secret = set_secret()
    return secret


# Generate uri of shared secret and convert it to a qrcode image
def get_secret_qr(totp: TOTP) -> PhotoImage:
    uri = totp.provisioning_uri(name=WINDOW_TITLE, issuer_name=WINDOW_TITLE)
    return PhotoImage(qr_make(uri))


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.totp = TOTP(get_secret())
        self.totp_qr = get_secret_qr(self.totp)
        self.create_widgets()
        self.pack()
        self.update_pin_label()
        self.set_scheduler()

    def create_widgets(self) -> None:
        # TOTP qrcode widget
        self.totp_qr_label = tk.Label(self)
        self.totp_qr_label['image'] = self.totp_qr
        self.totp_qr_label.grid(row=0, column=0, columnspan=2)

        # TOTP pin text, it change every 30 seconds
        self.pin_label_text = tk.StringVar()
        self.pin_label_text.set('Wait...')

        # TOTP pin widget
        pin_label = tk.Entry(self)
        pin_label['font'] = 'monospace 20 bold'
        pin_label['state'] = 'readonly'
        pin_label['textvariable'] = self.pin_label_text
        pin_label.grid(row=1, column=0)

        # Quit widget
        new_secret_btn = tk.Button(self)
        new_secret_btn['font'] = 'monospace 20'
        new_secret_btn['fg'] = 'red'
        new_secret_btn['text'] = 'NEW SECRET!'
        new_secret_btn['command'] = self.set_secret_and_update_pin_label
        new_secret_btn.grid(row=1, column=1)

    # Update pin label
    def update_pin_label(self) -> None:
        self.pin_label_text.set(self.totp.now())

    # Set scheduler to update pin label every 30 seconds
    def set_scheduler(self) -> None:
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.add_job(self.update_pin_label, trigger='cron', second=0)
        scheduler.add_job(self.update_pin_label, trigger='cron', second=30)

    # Set new secret and update the GUI
    def set_secret_and_update_pin_label(self) -> None:
        self.totp = TOTP(set_secret())
        self.totp_qr = get_secret_qr(self.totp)
        self.totp_qr_label['image'] = self.totp_qr
        self.update_pin_label()


if __name__ == '__main__':
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    app = Application(master=root)
    app.mainloop()
