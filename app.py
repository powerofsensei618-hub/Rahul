from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():
    return """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" type="text/css" href="https://sudor2spr.github.io/Documentation/assets/style.css">
    <title>SudoR2spr Repository</title>
    <link rel="icon" type="image/x-icon" href="https://raw.githubusercontent.com/SudoR2spr/SudoR2spr/main/assets/angel-op/Angel-ji.png">
</head>

<body>
    <div class="container">
        <p><b>Bot is running ✅</b></p>
    </div>
    <footer class="text-center py-3 mt-5">
        <div class="footer__copyright">
            <p class="footer__copyright-info">© 2024 Video Downloader. All rights reserved.</p>
        </div>
    </footer>
</body>

</html>
"""


@app.route('/health')
def health():
    return "ok", 200


if __name__ == "__main__":
    app.run()
