// Melhorias progressivas: o site funciona sem JavaScript; aqui só facilitamos a vida do usuário.
(function () {
  "use strict";

  // Checkout: esconde o endereço quando for retirada na loja.
  var radiosEntrega = document.querySelectorAll('input[name="tipo_entrega"]');
  var blocoEndereco = document.getElementById("bloco-endereco");
  function atualizarEndereco() {
    if (!blocoEndereco) return;
    var retirada = document.querySelector('input[name="tipo_entrega"][value="RETIRADA"]:checked');
    blocoEndereco.classList.toggle("oculto", !!retirada);
  }
  radiosEntrega.forEach(function (r) { r.addEventListener("change", atualizarEndereco); });
  atualizarEndereco();

  // Pagamento: esconde os dados do cartão quando for Pix.
  var radiosMetodo = document.querySelectorAll('input[name="metodo"]');
  var blocoCartao = document.getElementById("bloco-cartao");
  function atualizarCartao() {
    if (!blocoCartao) return;
    var pix = document.querySelector('input[name="metodo"][value="PIX"]:checked');
    blocoCartao.classList.toggle("oculto", !!pix);
  }
  radiosMetodo.forEach(function (r) { r.addEventListener("change", atualizarCartao); });
  atualizarCartao();

  // Máscaras simples
  function mascara(id, fn) {
    var el = document.getElementById(id);
    if (el) el.addEventListener("input", function () { el.value = fn(el.value); });
  }
  var digitos = function (v) { return v.replace(/\D/g, ""); };
  mascara("cep", function (v) { v = digitos(v).slice(0, 8); return v.length > 5 ? v.slice(0, 5) + "-" + v.slice(5) : v; });
  mascara("validade", function (v) { v = digitos(v).slice(0, 4); return v.length > 2 ? v.slice(0, 2) + "/" + v.slice(2) : v; });
  mascara("numero", function (v) { return document.getElementById("bloco-cartao") ? digitos(v).slice(0, 19).replace(/(.{4})/g, "$1 ").trim() : v; });
  mascara("uf", function (v) { return v.toUpperCase().replace(/[^A-Z]/g, "").slice(0, 2); });

  // PWA: registra o service worker (funciona em HTTPS ou localhost).
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(function () { /* sem suporte: ignora */ });
  }
})();
