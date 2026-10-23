#!/usr/bin/env bash
set -e

VENV_DIR="$HOME/.venvs/rom"
PREFIX="${PREFIX:-$HOME/bin}"

echo "Criando ambiente virtual em $VENV_DIR..."
python3 -m venv "$VENV_DIR"

echo "Instalando dependências..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -e .

mkdir -p "$PREFIX"

cat <<EOF > "$PREFIX/rom"
#!/usr/bin/env bash
exec "$VENV_DIR/bin/python" -m rom_cli.main "\$@"
EOF
chmod +x "$PREFIX/rom"

echo "Instalação concluída! Executável criado em $PREFIX/rom"
