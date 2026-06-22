/* ============================================
   LANGUAGE
   ============================================ */

const flags = document.querySelectorAll(".flag");

// DEV TODO: remove currentLanguage and localStorage after all JS files are migrated
let currentLanguage = "fr";

function getCurrentLanguage() {
  return window.location.pathname.startsWith("/en/") ? "en" : "fr";
}

function updateFlags() {
  currentLanguage = getCurrentLanguage();
  flags.forEach((flag) => {
    flag.classList.toggle(
      "active",
      flag.getAttribute("data-lang") === currentLanguage,
    );
  });
}

async function changeLanguage(lang, event = null) {
  if (event) event.preventDefault();

  currentLanguage = lang;
  localStorage.setItem("language", currentLanguage);
  updateFlags();

  document.dispatchEvent(
    new CustomEvent("languageChanged", { detail: { lang } }),
  );
}

/* ============================================
   MENU
   ============================================ */

// Fonction pour afficher le menu
function toggleMenu() {
  const menuContent = document.querySelector(".display-tablet-laptop");
  const menuButton = document.querySelector("#menu_button");
  const menuContentProduit = document.querySelector(".menu-content-produit");
  menuContent.classList.toggle("active");
  menuButton.classList.toggle("active");
  if (menuContentProduit.classList.contains("active")) {
    menuContentProduit.classList.remove("active");
  }
}

// Fermer le menu si on clique en dehors
document.addEventListener("click", function (event) {
  const menuButton = document.querySelector("#menu_button");
  const menuContent = document.querySelector(".display-tablet-laptop");
  const menuContentProduit = document.querySelector(".menu-content-produit");

  // Si le clic n'est ni sur le bouton du menu ni sur le contenu du menu et que le menu est actif
  if (
    !menuButton.contains(event.target) &&
    !menuContent.contains(event.target) &&
    menuContent.classList.contains("active")
  ) {
    menuContent.classList.remove("active");
    menuButton.classList.remove("active");
    if (menuContentProduit.classList.contains("active")) {
      menuContentProduit.classList.remove("active");
    }
  }
});

//fonction pour afficher le contact
function displayContact(event) {
  const ContactDiv = document.querySelector("#contact-form");
  const overlay = document.querySelector("#overlay");
  ContactDiv.style.display = "block";
  overlay.style.display = "block"; // Affiche l'overlay
}

// Fonction pour masquer le contact
function hideContact() {
  const ContactDiv = document.querySelector("#contact-form");
  const overlay = document.querySelector("#overlay");
  overlay.style.display = "none"; // Masque l'overlay
  ContactDiv.style.display = "none";
}

// Fonction pour fermer le contact et le modal si on clique sur l'overlay
document.addEventListener("click", function (event) {
  const overlay = document.querySelector("#overlay");
  if (overlay.contains(event.target)) {
    hideContact();
    closeModal();
  }
});

// Fontion au chargement de la page
document.addEventListener("DOMContentLoaded", function () {
  // Ecouteur d'evenement sur les images pour afficher une div avec toute les images
  const produits = document.querySelectorAll(".produit");
  produits.forEach((produit) => {
    const img = produit.querySelector("img"); // Sélectionner l'image principale
    const clickHint = produit.querySelector(".click-hint");
    if (img) {
      img.addEventListener("click", () => {
        const articleId = produit.getAttribute("data-product-id");
        if (!articleId) return;
        displayProductImages(articleId);
      });
      clickHint.addEventListener("click", () => {
        const articleId = produit.getAttribute("data-product-id");
        if (!articleId) return;
        displayProductImages(articleId);
      });
    }
  });
  initCart();
  if (
    window.location.pathname.includes("panier") ||
    window.location.pathname.includes("cart")
  ) {
    if (document.getElementById("order-total")) {
      const orderTotal = document.getElementById("order-total");
      if (orderTotal) {
        const total = parseFloat(orderTotal.textContent.replace(",", "."));
        orderTotal.textContent =
          currentLanguage === "en"
            ? total.toFixed(2)
            : total.toFixed(2).replace(".", ",");
      }
      updateInsurance();
      updateTotal();
      updateCartVisibility();
    }
  }
});

// Fonction pour récupérer le token CSRF depuis le meta tag
function getCSRFTokenFromMeta() {
  const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
  return csrfTokenMeta ? csrfTokenMeta.getAttribute("content") : "";
}
function initCart() {
  if (!localStorage.getItem("cart")) {
    localStorage.setItem("cart", JSON.stringify([]));
  }
}
// Ajouter un produit au panier
function addToCart(articleId) {
  fetch(`/api/cart/add_to_cart/${articleId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFTokenFromMeta(),
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Sauvegarde dans le localStorage pour qu'il persiste entre les sessions
        localStorage.setItem("cart_uuid", data.cart_uuid);
        let cart = JSON.parse(localStorage.getItem("cart")) || [];
        cart.push({ id: articleId });
        localStorage.setItem("cart", JSON.stringify(cart));
        alert(data.message);
        updateProductList(articleId); // Met à jour la liste des produits en retirant celui qui a été ajouté
        closeModal();
        document.body.dispatchEvent(new Event("cartUpdated"));
      } else {
        alert("Erreur : " + data.message);
      }
    })
    .catch((error) => {
      console.error("Erreur lors de l'ajout au panier:", error);
    });
}
function updateProductList(articleId) {
  // Trouver l'élément HTML représentant cet article et le supprimer
  const allProducts = Array.from(document.querySelectorAll(".produit"));
  const productElement = allProducts.find(
    (product) => product.getAttribute("data-product-id") === articleId,
  );

  if (productElement) {
    productElement.style.display = "none"; // Masquer l'élément du DOM
  }
}

// Au chargement de la page, vérifier si l'UUID du panier est dans localStorage
window.onload = function () {
  const cart_uuid = localStorage.getItem("cart_uuid"); // Récupère l'UUID depuis localStorage
  if (cart_uuid) {
    window.cart_uuid = cart_uuid; // Assigner à la variable globale pour usage ultérieur
    console.log(
      "UUID du panier récupéré depuis localStorage:",
      window.cart_uuid,
    );
  } else {
    console.log("Aucun UUID trouvé dans localStorage.");
  }
};
// Fonction pour mettre à jour l'affichage du panier
function updateCartVisibility() {
  const orderTotal = parseFloat(
    document.getElementById("order-total").textContent.replace(",", "."),
  );
  const cartSection = document.querySelector(".cart-container");
  const emptyCartMessage = document.querySelector("#empty-section");

  // Si le total est 0 ou indéfini, on considère le panier vide
  if (orderTotal <= 0 || isNaN(orderTotal)) {
    cartSection.style.display = "none";
    emptyCartMessage.style.display = "block";
  } else {
    cartSection.style.display = "block";
    emptyCartMessage.style.display = "none";
  }
}
// Fonction pour vider le panier
function clearCart() {
  fetch("/api/cart/empty_cart/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFTokenFromMeta(),
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Réinitialise le localStorage
        localStorage.removeItem("cart");
        const addInsurance = document.getElementById("add-insurance");
        addInsurance.checked = false;
        alert(data.message);
        const formattedZero = currentLanguage === "en" ? "0.00" : "0,00";
        document.getElementById("order-total").textContent = formattedZero;
        document.getElementById("total-amount").textContent = formattedZero;
        updateCartVisibility();
        initCart();
        document.body.dispatchEvent(new Event("cartUpdated"));
      } else {
        alert("Erreur lors de la suppression du panier.");
      }
    });
}

// Fonction pour nettoyer le filtre
function cleanFilter() {
  // Redirige vers l'URL de base sans paramètres GET
  window.location.href = window.location.pathname;
}

// Fonction pour supprimer un article du panier
function remove_from_cart(articleId) {
  fetch(`/api/cart/remove_from_cart/${articleId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCSRFTokenFromMeta(),
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        let cart = JSON.parse(localStorage.getItem("cart")) || [];
        cart = cart.filter((item) => parseInt(item.id) !== parseInt(articleId));
        localStorage.setItem("cart", JSON.stringify(cart));
        const addInsurance = document.getElementById("add-insurance");
        let orderTotal = parseFloat(
          document.getElementById("order-total").textContent.replace(",", "."),
        );
        const priceArticle = parseFloat(data.article.price.toFixed(2));
        orderTotal -= priceArticle;
        // Formater selon la langue
        const formattedTotal =
          currentLanguage === "en"
            ? orderTotal.toFixed(2)
            : orderTotal.toFixed(2).replace(".", ",");
        document.getElementById("order-total").textContent = formattedTotal;
        if (orderTotal < 25) {
          addInsurance.checked = false;
        }
        updateInsurance();
        updateTotal();
        document.body.dispatchEvent(new Event("cartUpdated"));
        alert(data.message);
      } else {
        alert("Erreur lors de la suppression de l'article.");
      }
    })
    .finally(() => {
      updateCartVisibility();
    });
}

let currentImageIndex = 0; // Index de l'image actuelle
let images = []; // Tableau pour stocker les images

// Fonction pour afficher les images d'un article avec le nom de l'article
function displayProductImages(articleId) {
  fetch(`/api/catalog/get_product_images/${articleId}/`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      document.getElementById("nom-article").textContent = data.nom;

      const descriptionEl = document.getElementById("description-article");
      if (data.description) {
        descriptionEl.textContent = data.description;
      } else {
        descriptionEl.textContent =
          currentLanguage === "en"
            ? "No description available"
            : "Aucune description disponible";
      }
      const price = Number(data.prix);
      const discount = Number(data.discount || 0);
      const priceEl = document.getElementById("prix-article");
      const newPriceEl = document.getElementById("new_price");
      const newPriceH3El = document.getElementById("new_price_h3");

      priceEl.textContent = price.toFixed(2).replace(".", ",") + " €";

      const promoWidget = document.getElementById("promo-widget");

      if (discount > 0) {
        promoWidget.style.display = "block";
        newPriceH3El.style.display = "INLINE";
        const newPrice = price - discount;

        priceEl.style.textDecoration = "line-through";
        priceEl.style.textDecorationThickness = "3px";
        priceEl.style.textDecorationColor = "#da0410";
        newPriceEl.textContent = newPrice.toFixed(2).replace(".", ",") + " €";
      } else {
        priceEl.style.textDecoration = "none";
        newPriceEl.textContent = "";
        promoWidget.style.display = "none";
        newPriceH3El.style.display = "none";
      }

      // --- Bouton panier ---
      const addToCartButton = document.getElementById("id_add_to_cart_button");
      if (addToCartButton) {
        if (
          window.location.pathname.includes("panier") ||
          window.location.pathname.includes("cart") ||
          data.en_attente_dans_panier ||
          data.sur_commande
        ) {
          addToCartButton.style.display = "none";
        } else {
          addToCartButton.style.display = "block";
          addToCartButton.style.width = "fit-content";
          addToCartButton.dataset.productId = articleId;
        }
      }

      // --- Images ---
      images = data.images || [];
      currentImageIndex = 0;

      if (images.length > 0) {
        document.getElementById("current-image").src = images[0];
        document.getElementById("zoomImage").src = images[0];
      }

      // --- Modal ---
      document.getElementById("overlay").style.display = "block";
      document.getElementById("modal").style.display = "block";
    })
    .catch((error) => {
      console.error("Fetch error:", error);
    });
}

// Fonction pour changer d'image
function changeImage(direction) {
  currentImageIndex += direction; // Changer l'index
  if (currentImageIndex < 0) {
    currentImageIndex = images.length - 1; // Revenir à la dernière image
  } else if (currentImageIndex >= images.length) {
    currentImageIndex = 0; // Revenir à la première image
  }
  document.getElementById("current-image").src = images[currentImageIndex]; // Mettre à jour l'image affichée
  document.getElementById("zoomImage").src = images[currentImageIndex]; // Mettre à jour l'image affichée dans le zoom
}

// Fonction pour fermer la modale
function closeModal() {
  const modal = document.getElementById("modal");
  const overlay = document.getElementById("overlay");
  overlay.style.display = "none"; // Masque l'overlay
  modal.style.display = "none";
}

// Fonction pour mettre à jour les frais de port
function updateShippingCost() {
  const currentLang = localStorage.getItem("language") || "fr";
  const shippingOption = document.getElementById("add-shipping");
  const shippingCostSpan = document.getElementById("shipping-cost");
  if (shippingOption.checked) {
    const shippingCost = 10;
    const formattedShippingCost =
      currentLang === "en"
        ? shippingCost.toFixed(2)
        : shippingCost.toFixed(2).replace(".", ",");
    shippingCostSpan.textContent = formattedShippingCost;
  } else {
    const shippingCost = 5;
    const formattedShippingCost =
      currentLang === "en"
        ? shippingCost.toFixed(2)
        : shippingCost.toFixed(2).replace(".", ",");
    shippingCostSpan.textContent = formattedShippingCost;
  }
}
// Fonction pour mettre à jour l'assurance

function updateInsurance() {
  const orderTotalElement = document.getElementById("order-total");

  if (!orderTotalElement) {
    return;
  }

  const orderTotal = parseFloat(
    orderTotalElement.textContent.replace(",", "."),
  );
  const insuranceOption = document.getElementById("insurance-option"); // Checkbox assurance optionnelle
  const mandatoryInsurance = document.getElementById("mandatory-insurance"); // Assurance obligatoire
  const insuranceCostSpan = document.getElementById("insurance-cost"); // Prix assurance optionnelle
  const mandatoryInsuranceCostSpan = document.getElementById(
    "mandatory-insurance-cost",
  ); // Prix assurance obligatoire
  const insurance25Euros = document.getElementById("insurance_25_euros"); // Message pour 25€ d'assurance incluse
  const insurance25Euros2 = document.getElementById("insurance_25_euros_2"); // Message pour 25€ d'assurance incluse
  const insurance = document.getElementById("insurance");
  const upTo500 = document.getElementById("mandatory_insurance_4");
  const insurance_info = document.getElementById("insurance_info");

  // Cacher toutes les options par défaut
  insuranceOption.classList.add("hidden");
  mandatoryInsurance.classList.add("hidden");
  insurance25Euros.classList.remove("hidden");
  insurance25Euros2.classList.remove("hidden");
  insurance.classList.remove("hidden");
  upTo500.classList.add("hidden");
  insuranceCostSpan.textContent = "0,00";
  mandatoryInsuranceCostSpan.textContent = "0,00";
  insurance_info.classList.add("hidden");

  // Fonction helper pour formater les nombres selon la langue
  const formatNumber = (num) =>
    currentLanguage === "en"
      ? num.toFixed(2)
      : num.toFixed(2).replace(".", ",");

  // 1. Gestion de l'assurance optionnelle entre 25 € et 50 €
  if (orderTotal > 25 && orderTotal <= 50) {
    insuranceOption.classList.remove("hidden"); // Afficher l'option d'assurance
    insurance.classList.add("hidden");
    if (insuranceOption.checked) {
      insuranceCostSpan.textContent = formatNumber(2); // Coût fixe pour cette tranche
    }
  }

  // 2. Gestion de l'assurance obligatoire au-delà de 50 €
  if (orderTotal > 50) {
    insurance25Euros.classList.add("hidden");
    insurance25Euros2.classList.add("hidden");
    mandatoryInsurance.classList.remove("hidden");
    insurance_info.classList.remove("hidden");

    // Définir le coût de l'assurance obligatoire en fonction du total
    let insuranceAmount = 3.5;
    if (orderTotal > 500) {
      upTo500.classList.remove("hidden");
      insuranceAmount = 8;
    } else if (orderTotal > 375) {
      insuranceAmount = 8;
    } else if (orderTotal > 250) {
      insuranceAmount = 6.5;
    } else if (orderTotal > 125) {
      insuranceAmount = 5;
    }
    mandatoryInsuranceCostSpan.textContent = formatNumber(insuranceAmount);
    insuranceCostSpan.textContent = formatNumber(insuranceAmount);
  }
}
// Fonction pour mettre à jour le total
function updateTotal() {
  const currentLang = localStorage.getItem("language") || "fr";
  const orderTotalElement = document.getElementById("order-total");
  const insuranceCostElement = document.getElementById("insurance-cost");
  const totalAmountElement = document.getElementById("total-amount");

  if (!orderTotalElement || !insuranceCostElement || !totalAmountElement) {
    return;
  }

  const orderTotal = parseFloat(
    orderTotalElement.textContent.replace(",", "."),
  );
  const insuranceCost =
    parseFloat(insuranceCostElement.textContent.replace(",", ".")) || 0;

  const addInsurance =
    document.getElementById("add-insurance")?.checked || false;
  const addShipping = document.getElementById("add-shipping")?.checked || false;
  let totalAmount = orderTotal + 5.0 + insuranceCost;

  if (addInsurance && orderTotal > 25 && orderTotal <= 50) {
    totalAmount += 2.0;
  }
  if (addShipping) {
    totalAmount += 5.0;
  }
  const formattedTotal =
    currentLang === "en"
      ? totalAmount.toFixed(2)
      : totalAmount.toFixed(2).replace(".", ",");

  totalAmountElement.textContent = formattedTotal;
}

// Fonction pour gérer le checkout
function handleCheckout() {
  const acceptCGV = document.getElementById("accept-cgv").checked;
  const addInsurance = document.getElementById("add-insurance").checked;
  const addShipping = document.getElementById("add-shipping").checked;
  const errorMessage = document.getElementById("error-message");
  let orderTotal = document.getElementById("total-amount").textContent;
  if (currentLanguage == "fr") {
    orderTotal = orderTotal.replace(",", ".");
  }
  if (!acceptCGV) {
    errorMessage.classList.remove("hidden");
    return;
  }

  errorMessage.classList.add("hidden");

  // Récupérer l'UUID du panier depuis le localStorage
  const cart_uuid = localStorage.getItem("cart_uuid");

  if (!cart_uuid) {
    console.error("L'UUID du panier est introuvable.");
    return;
  }
  // Redirige vers Stripe avec le montant total
  window.location.href = `/api/cart/checkout/?front_total=${orderTotal}&cart_uuid=${cart_uuid}&insurance=${addInsurance ? 1 : 0}&shipping=${addShipping ? 1 : 0}&acceptCGV=${acceptCGV ? 1 : 0}`;
}
// débug

function debugElements() {
  console.log("🔍 Debug des éléments DOM :");
  console.log("order-total :", document.getElementById("order-total"));
  console.log("insurance-cost :", document.getElementById("insurance-cost"));
  console.log("add-insurance :", document.getElementById("add-insurance"));
  console.log("total-amount :", document.getElementById("total-amount"));
}

function scrollToProducts() {
  const productsSection = document.getElementById("pagination-top");
  const offsetTop = productsSection.offsetTop - 62.5;
  if (productsSection) {
    window.scrollTo({
      top: offsetTop,
      behavior: "smooth",
    });
  }
}

// Sortir les evenement onclick
if (document.getElementById("contact_link")) {
  document
    .getElementById("contact_link")
    .addEventListener("click", function () {
      displayContact();
    });
}

if (document.getElementById("close-btn")) {
  document.getElementById("close-btn").addEventListener("click", function () {
    hideContact();
  });
}

if (document.getElementById("footer_contact")) {
  document
    .getElementById("footer_contact")
    .addEventListener("click", function () {
      displayContact();
    });
}

if (document.getElementById("menu_button")) {
  document.getElementById("menu_button").addEventListener("click", function () {
    toggleMenu();
  });
}

if (document.getElementById("contact_button")) {
  document
    .getElementById("contact_button")
    .addEventListener("click", function () {
      displayContact();
    });
}

if (document.getElementById("clear_cart")) {
  document.getElementById("clear_cart").addEventListener("click", function () {
    clearCart();
  });
}

if (document.getElementById("add-insurance")) {
  document
    .getElementById("add-insurance")
    .addEventListener("change", function () {
      updateTotal();
    });
}
if (document.getElementById("add-shipping")) {
  document
    .getElementById("add-shipping")
    .addEventListener("change", function () {
      updateShippingCost();
      updateTotal();
    });
}

if (document.getElementById("checkout")) {
  document.getElementById("checkout").addEventListener("click", function () {
    handleCheckout();
  });
}

if (document.getElementById("close-button")) {
  document
    .getElementById("close-button")
    .addEventListener("click", function () {
      closeModal();
    });
}

if (document.getElementById("prev-button")) {
  document.getElementById("prev-button").addEventListener("click", function () {
    changeImage(-1);
  });
}

if (document.getElementById("next-button")) {
  document.getElementById("next-button").addEventListener("click", function () {
    changeImage(1);
  });
}

if (document.getElementById("clean_filter")) {
  document
    .getElementById("clean_filter")
    .addEventListener("click", function () {
      cleanFilter();
    });
}

document.addEventListener("click", function (event) {
  if (event.target && event.target.matches(".add_to_cart_button")) {
    const articleId = event.target.getAttribute("data-product-id");
    if (!articleId) return;
    addToCart(articleId);
  }
});

document.addEventListener("click", function (event) {
  if (event.target && event.target.matches(".delete_button")) {
    const articleId = event.target.getAttribute("data-product-id");
    if (!articleId) return;
    remove_from_cart(articleId);
  }
});

document.addEventListener("languageChanged", function () {
  if (
    window.location.pathname.includes("panier") ||
    window.location.pathname.includes("cart")
  ) {
    updateInsurance();
    updateTotal();
  }
});

if (document.getElementById("see_products_button")) {
  document
    .getElementById("see_products_button")
    .addEventListener("click", function () {
      scrollToProducts();
    });
}

// Zoom dans modal
if (document.getElementById("imageContainer")) {
  document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("imageContainer");
    const baseImage = document.getElementById("current-image");
    const loupe = document.getElementById("loupe");
    const zoomImage = document.getElementById("zoomImage");
    const zoom = 2; // facteur de zoom

    container.addEventListener("mousemove", function (e) {
      const rect = baseImage.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      if (
        x < 0 ||
        y < 0 ||
        x > rect.width ||
        y > rect.height ||
        window.innerWidth < 768
      ) {
        loupe.style.display = "none";
        return;
      }
      loupe.style.display = "block";

      // Positionner la loupe
      const loupeWidth = loupe.offsetWidth;
      const loupeHeight = loupe.offsetHeight;
      loupe.style.left = `${x - loupeWidth / 2}px`;
      loupe.style.top = `${y - loupeHeight / 2}px`;

      // Synchroniser la taille de l'image de zoom
      zoomImage.src = baseImage.src;
      zoomImage.style.width = `${baseImage.offsetWidth * zoom}px`;
      zoomImage.style.height = `${baseImage.offsetHeight * zoom}px`;

      // Positionner l'image zoomée à l'intérieur de la loupe
      const zoomX = -x * zoom + loupeWidth / 2;
      const zoomY = -y * zoom + loupeHeight / 2;

      zoomImage.style.left = `${zoomX}px`;
      zoomImage.style.top = `${zoomY}px`;
    });

    container.addEventListener("mouseleave", function () {
      loupe.style.display = "none";
    });
  });
}

/* ============================================
   EVENT LISTENERS
   ============================================ */

document.addEventListener("DOMContentLoaded", () => {
  const lang = getCurrentLanguage() || "fr";

  changeLanguage(lang);
});
