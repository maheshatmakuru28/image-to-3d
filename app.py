<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>3D Image Studio | Image to 3D Converter</title>

<style>
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: Arial, sans-serif;
    background: #080d1b;
    color: white;
    min-height: 100vh;
}

header {
    padding: 22px 7%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #202b45;
}

.logo {
    font-size: 25px;
    font-weight: bold;
    color: #60a5fa;
}

.badge {
    background: #142747;
    color: #93c5fd;
    padding: 9px 14px;
    border-radius: 20px;
    font-size: 12px;
}

.hero {
    text-align: center;
    padding: 45px 15px 25px;
}

.hero h1 {
    font-size: clamp(30px, 5vw, 48px);
    margin-bottom: 15px;
}

.hero h1 span {
    color: #60a5fa;
}

.hero p {
    color: #a6b3cc;
    line-height: 1.7;
}

.container {
    width: min(1100px, 92%);
    margin: 20px auto 50px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 22px;
}

.card {
    background: #111a2e;
    border: 1px solid #263451;
    padding: 25px;
    border-radius: 18px;
}

.card h2 {
    font-size: 20px;
    margin-bottom: 20px;
}

.upload-box {
    min-height: 220px;
    border: 2px dashed #45618d;
    border-radius: 15px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 20px;
    cursor: pointer;
    background: #0b1427;
}

.upload-box:hover {
    border-color: #60a5fa;
}

.upload-icon {
    font-size: 45px;
    margin-bottom: 15px;
}

.upload-box p {
    color: #a6b3cc;
    margin-top: 10px;
    font-size: 13px;
}

input[type="file"] {
    display: none;
}

button {
    border: none;
    cursor: pointer;
    padding: 13px 18px;
    border-radius: 10px;
    font-weight: bold;
    font-size: 14px;
}

.primary {
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    color: white;
    width: 100%;
    margin-top: 18px;
}

.secondary {
    background: #24334f;
    color: white;
}

button:hover {
    opacity: 0.85;
}

.preview {
    min-height: 260px;
    border-radius: 14px;
    background:
        radial-gradient(circle, #243b61 0%, #0b1221 75%);
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    perspective: 1000px;
    padding: 25px;
}

#previewImage {
    max-width: 100%;
    max-height: 320px;
    object-fit: contain;
    border
