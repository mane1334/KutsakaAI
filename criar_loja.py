from ferramentas import criar_estrutura_pastas

estrutura = {
    "index.html": """<!DOCTYPE html>
<html>
<head>
    <title>Loja Online</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <h1>Nossa Loja</h1>
    </header>
    <main>
        <div class="produtos"></div>
    </main>
    <script src="js/main.js"></script>
</body>
</html>""",
    "css": {
        "style.css": """body {
    font-family: Arial;
    margin: 0;
}
.produtos {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    padding: 20px;
}"""
    },
    "js": {
        "main.js": """document.addEventListener('DOMContentLoaded', () => {
    console.log('Loja carregada!');
});"""
    },
    "img": {
        "produtos": {
            "produto1.jpg": "",
            "produto2.jpg": ""
        }
    }
}

criar_estrutura_pastas('c:/teste', estrutura) 