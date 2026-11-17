from decimal import Decimal

from app.extensions import db
from app.models import Categoria, Cupcake, Usuario

CATALOGO = {
    "Clássicos": [
        ("Baunilha com Buttercream", "Massa fofinha de baunilha com cobertura cremosa de buttercream.", "9.50", "🧁"),
        ("Chocolate Belga", "Massa de cacau com ganache de chocolate belga meio amargo.", "11.00", "🍫"),
        ("Red Velvet", "Clássico red velvet com cobertura de cream cheese.", "12.50", "❤️"),
    ],
    "Frutados": [
        ("Limão Siciliano", "Massa cítrica com recheio de curd de limão e merengue.", "11.50", "🍋"),
        ("Morango Fresco", "Massa de baunilha, recheio de geleia e topo de morangos.", "12.00", "🍓"),
    ],
    "Gourmet": [
        ("Doce de Leite com Flor de Sal", "Recheio de doce de leite artesanal e flor de sal.", "13.00", "🥛"),
        ("Pistache", "Massa de pistache com creme de pistache e castanhas.", "15.00", "🌰"),
        ("Café com Caramelo", "Massa de café com caramelo salgado e grãos crocantes.", "13.50", "☕"),
    ],
}


def popular(admin_email: str, admin_senha: str) -> None:
    for nome_cat, itens in CATALOGO.items():
        cat = db.session.scalar(db.select(Categoria).where(Categoria.nome == nome_cat))
        if cat is None:
            cat = Categoria(nome=nome_cat)
            db.session.add(cat)
            db.session.flush()
        for nome, desc, preco, emoji in itens:
            if not db.session.scalar(db.select(Cupcake).where(Cupcake.nome == nome)):
                db.session.add(Cupcake(categoria_id=cat.id, nome=nome, descricao=desc,
                                       preco=Decimal(preco), emoji=emoji))
    if not db.session.scalar(db.select(Usuario).where(Usuario.email == admin_email)):
        admin = Usuario(nome="Administrador", email=admin_email, telefone="11999999999",
                        is_admin=True)
        admin.definir_senha(admin_senha)
        db.session.add(admin)
    db.session.commit()
