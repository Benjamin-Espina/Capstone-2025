// Función que se activa al hacer clic en el ícono del menú
function myFunction(x) {
  // Alterna la clase "change" en el elemento clicado (x), para animar
  x.classList.toggle("change");
   // Obtiene el elemento con ID "menu-botones", que contiene las opciones del menú desplegable
  const menu = document.getElementById("menu-botones");
  // Alterna la clase "show" en el menú, para mostrarlo u ocultarlo (según su estado actual)
  menu.classList.toggle("show");
}
