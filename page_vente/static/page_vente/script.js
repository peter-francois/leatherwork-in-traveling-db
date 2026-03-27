const flags = document.querySelectorAll('.flag');

let currentLanguage = localStorage.getItem('language') || 'fr';

async function getDocumentContent(documentType, lang) {
    try {
        const response = await fetch(`/api/get_document_content/${documentType}/${lang}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.text();  // Récupérer le HTML en tant que texte
    } catch (error) {
        console.error("Error fetching document content:", error);
        return "";
    }
}

function getLanguageFromCookie() {
    const match = document.cookie.match(/(?:^|;\s*)django_language=([^;]+)/);
    return match ? match[1] : null;
}
// Fonction pour changer la langue

async function changeLanguage(lang, event = null, initial = false) {
    if (event) event.preventDefault(); // Empêche rechargement


    try {
        
        // Mettre à jour la langue dans le stockage local
        currentLanguage = lang;
        localStorage.setItem('language', currentLanguage);
        
        // Mettre à jour les contenus des documents
        const documentPromises = [];
        
        const documents = {
            'cgv_content': 'CGV',
            'cookies_content': 'Cookies',
            'legal_mentions_content': 'LegalMentions',
            'privacy_policy_content': 'PrivacyPolicy'
        };

        for (const [elementId, docType] of Object.entries(documents)) {
            const element = document.getElementById(elementId);
            if (element) {
                documentPromises.push(
                    getDocumentContent(docType, lang)
                        .then(content => {
                            element.innerHTML = content;
                        })
                );
            }
        }

        // Attendre que tous les documents soient chargés
        await Promise.all(documentPromises);

        // Mise à jour de l'interface
        updateFlags(lang);

        // Mettre à jour les prix si on est sur la page panier
        if (window.location.pathname.includes('panier') || window.location.pathname.includes('cart')) {
            const orderTotal = document.getElementById('order-total');
            const insuranceCost = document.getElementById('insurance-cost');
            const totalAmount = document.getElementById('total-amount');
            
            if (orderTotal && insuranceCost && totalAmount) {
                const total = parseFloat(orderTotal.textContent.replace(',', '.'));
                orderTotal.textContent = lang === 'en' ? 
                    total.toFixed(2) : 
                    total.toFixed(2).replace('.', ',');
                
                // Forcer la mise à jour de l'assurance et du total

                await Promise.resolve(); // Attendre le prochain cycle
                await updateInsurance();
                await updateTotal();
        }
    }
         // Déclencher l'événement après les mises à jour
         document.dispatchEvent(new Event('languageChanged'));

    } catch (error) {
        console.error('Error during language change:', error);
    }
}

// Fonction séparée pour mettre à jour l'etat actif des drapeaux
function updateFlags(lang) {
    flags.forEach(flag => {
        flag.classList.toggle('active', flag.getAttribute('data-lang') === lang);
    });
}
document.addEventListener('DOMContentLoaded', () => {
    // Langue déjà définie par Django via cookie
    const lang = getLanguageFromCookie() || 'fr';  // fallback au cas où

    // Lancer la logique JS avec cette langue (mais sans reload, ni changement d'URL)
    changeLanguage(lang, null, true); // Le paramètre `initial = true` empêche le pushState
});


// Fonction pour afficher le menu
function toggleMenu() {
    const menuContent = document.querySelector('.display-tablet-laptop');
    const menuButton = document.querySelector('#menu_button');
    const menuContentProduit = document.querySelector('.menu-content-produit');
    menuContent.classList.toggle('active');
    menuButton.classList.toggle('active');
    if (menuContentProduit.classList.contains('active')) {
        menuContentProduit.classList.remove('active');
    }
}

// Fermer le menu si on clique en dehors
document.addEventListener('click', function(event) {
    const menuButton = document.querySelector('#menu_button');
    const menuContent = document.querySelector('.display-tablet-laptop');
    const menuContentProduit = document.querySelector('.menu-content-produit');
    
    // Si le clic n'est ni sur le bouton du menu ni sur le contenu du menu et que le menu est actif
    if (!menuButton.contains(event.target) && !menuContent.contains(event.target) && menuContent.classList.contains('active')) {
        menuContent.classList.remove('active');
        menuButton.classList.remove('active');
        if (menuContentProduit.classList.contains('active')) {
            menuContentProduit.classList.remove('active');
        }
    }
});



//fonction pour afficher le contact
function displayContact(event) {

    const ContactDiv = document.querySelector('#contact-form');
    const overlay = document.querySelector('#overlay');
    ContactDiv.style.display = 'block';
    overlay.style.display = 'block'; // Affiche l'overlay
}

// Fonction pour masquer le contact
function hideContact() {
    const ContactDiv = document.querySelector('#contact-form');
    const overlay = document.querySelector('#overlay');
    overlay.style.display = 'none'; // Masque l'overlay
    ContactDiv.style.display = 'none';
}

// Fonction pour fermer le contact et le modal si on clique sur l'overlay
document.addEventListener('click', function(event) {
    const overlay = document.querySelector('#overlay');
    if (overlay.contains(event.target)) {
        hideContact();
        closeModal();
    }
});

// Fontion au chargement de la page
document.addEventListener('DOMContentLoaded', function () {
    // Ecouteur d'evenement sur les images pour afficher une div avec toute les images
    const produits = document.querySelectorAll('.produit');
    produits.forEach(produit => {
        const img = produit.querySelector('img'); // Sélectionner l'image principale
        const clickHint = produit.querySelector('.click-hint');
        if (img) {
            img.addEventListener('click', () => {
                const articleId = produit.getAttribute('data-product-id');
                if (!articleId) return;
                displayProductImages(articleId);
            });
            clickHint.addEventListener('click', () => {
                const articleId = produit.getAttribute('data-product-id');
                if (!articleId) return;
                displayProductImages(articleId);
            });
        }
    });
    displayCart();
    initCart();
    updateTextCartButton(); 
    if (window.location.pathname.includes('panier') || window.location.pathname.includes('cart')){
        if(document.getElementById('order-total')){
            const orderTotal = document.getElementById('order-total');
            if (orderTotal) {
                const total = parseFloat(orderTotal.textContent.replace(',', '.'));
                orderTotal.textContent = currentLanguage === 'en' ? 
                    total.toFixed(2) : 
                    total.toFixed(2).replace('.', ',');
            }
            updateInsurance();
            updateTotal();
            updateCartVisibility();
            
        }
    }
});

// Fonction pour afficher les articles du panier
function displayCart() {
    fetch('/api/cart_detail/')
        .then(response => response.json())
        .then(data => {
            let listeArticles = document.getElementById('liste-articles');
            if (listeArticles) {
                const formatNumber = (num) => currentLanguage === 'en' ? 
                    num.toFixed(2) : 
                    num.toFixed(2).replace('.', ',');
                listeArticles.innerHTML = ''; 
                data.cart.forEach(article => {
                    const translations_front = JSON.parse(document.getElementById("translations").textContent);
                    let li = document.createElement('li');
                    let img = document.createElement('img');
                    let clickHint = document.createElement('p');
                    clickHint.textContent = '👆 ' + translations_front.click_hint;
                    clickHint.classList.add('click-hint');
                    clickHint.onclick = () => displayProductImages(article.id);
                    let h3 = document.createElement('h3');
                    let p = document.createElement('p');
                    p.textContent = translations_front.price;
                    p.style.margin = "0px";
                    let span = document.createElement('span');
                    let span2 = document.createElement('span');
                    span.textContent = formatNumber(article.prix);;
                    span2.textContent = `€ (x${article.quantity})`;
                    h3.textContent = `${article.nom}`;
                    p.appendChild(span);
                    p.appendChild(span2);
                    img.onclick = () => displayProductImages(article.id);
                    img.alt = `${article.nom}`;

                    let button = document.createElement('button');
                    button.textContent = translations_front.delete_button;
                    button.onclick = () => remove_from_cart(article.id);
                    button.classList.add('page-button', 'delete_button');
                    li.appendChild(h3);
                    if (article.image1) {
                        img.src = article.image1;
                        img.alt = `${article.nom}`;
                        li.appendChild(img);
                        li.appendChild(clickHint);
                    }
                    else if (article.image2) {
                        img.src = article.image2;
                        img.alt = `${article.nom}`;
                        li.appendChild(img);
                    }
                    else if (article.image3) {
                        img.src = article.image3;
                        img.alt = `${article.nom}`;
                        li.appendChild(img);
                        li.appendChild(clickHint);
                    }
                    else if (article.image4) {
                        img.src = article.image4;
                        img.alt = `${article.nom}`;
                        li.appendChild(img);
                        li.appendChild(clickHint);
                    }
                    else if (article.image5) {
                        img.src = article.image5;
                        img.alt = `${article.nom}`;
                        li.appendChild(img);
                        li.appendChild(clickHint);
                    }
                    else if (article.image6) {
                        img.src = article.image6;
                        img.alt = `${article.nom}`;
                        li.appendChild(img);
                        li.appendChild(clickHint);
                    }
                    else {
                        img.src = ''; // Aucune image disponible
                        let p = document.createElement('p');
                        p.classList.add('no-image');
                        p.textContent = translations_front.no_image;

                    }
                    if(article.discount > 0.0){
                        let promoWidget = document.createElement("p");
                        promoWidget.classList.add("promo-widget");
                        promoWidget.textContent = "Promo";
                        li.append(promoWidget);
                        let new_price = document.createElement("p");
                        new_price.style.margin = "0px";
                        new_price.textContent = `Nouveau prix: ${formatNumber(article.prix - article.discount)}€`;
                        li.appendChild(new_price);
                        p.style.textDecoration = "line-through";
                        p.style.textDecorationThickness = "3px";
                        p.style.textDecorationColor = "#da0410";
                    }
                    else{
                        p.style.textDecoration = 'none';
                    }
                    li.appendChild(p);
                    li.appendChild(button);
                    listeArticles.appendChild(li);
                });
                

            }
        }).catch(error => console.error('Erreur lors de la récupération du panier:', error));
}

// Fonction pour récupérer le token CSRF depuis le meta tag
function getCSRFTokenFromMeta() {
    const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
    return csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : '';
}
function initCart() {
    if (!localStorage.getItem('cart')) {
        localStorage.setItem('cart', JSON.stringify([]));
    }
}
// Ajouter un produit au panier
function addToCart(articleId) {
    fetch(`/api/add_to_cart/${articleId}/`, { 
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFTokenFromMeta(),
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Sauvegarde dans le localStorage pour qu'il persiste entre les sessions
                localStorage.setItem('cart_uuid', data.cart_uuid);
                let cart = JSON.parse(localStorage.getItem('cart')) || [];
                cart.push({ id: articleId});
                localStorage.setItem('cart', JSON.stringify(cart));
                alert(data.message);
                updateTextCartButton(); 
                updateProductList(articleId);  // Met à jour la liste des produits en retirant celui qui a été ajouté
                closeModal();
            } else {
                alert("Erreur : " + data.message);
            }
        }).catch(error => {
            console.error('Erreur lors de l\'ajout au panier:', error);
        });
}
function updateProductList(articleId) {
    // Trouver l'élément HTML représentant cet article et le supprimer
    const allProducts = Array.from(document.querySelectorAll('.produit')); 
    const productElement = allProducts.find(product => product.getAttribute('data-product-id') === articleId);
    
    if (productElement) {
        productElement.style.display = 'none';  // Masquer l'élément du DOM
    }
}

// Fonction pour obtenir le nombre d'articles dans le panier
async function getNumberOfProductsInCart() {
    const response = await fetch(`/api/get_number_of_products_in_cart/`, { 
        method: 'GET',
        headers: {
            'X-CSRFToken': getCSRFTokenFromMeta(),
            'Content-Type': 'application/json'
        }
    });

    const data = await response.json();
    // Retourne directement le nombre d'articles
    if (data.success) {
        return data.number_of_products;
    } else {
        return 0; // Retourne 0 si il y a une erreur
    }
}

// Fonction pour mettre à jour l'affichage du nombre d'articles dans le panier
async function updateTextCartButton() {
    const textCartButton = document.getElementById('text-cart-button');
    if (!textCartButton) return;

    // Récupérer le nombre d'articles dans le panier
    const numberOfProducts = await getNumberOfProductsInCart();
    
    // Mettre à jour l'affichage du bouton
    textCartButton.textContent = numberOfProducts;

}

// Au chargement de la page, vérifier si l'UUID du panier est dans localStorage
window.onload = function() {
    const cart_uuid = localStorage.getItem('cart_uuid'); // Récupère l'UUID depuis localStorage
    if (cart_uuid) {
        window.cart_uuid = cart_uuid; // Assigner à la variable globale pour usage ultérieur
        console.log("UUID du panier récupéré depuis localStorage:", window.cart_uuid);
    } else {
        console.log("Aucun UUID trouvé dans localStorage.");
    }
};
// Fonction pour mettre à jour l'affichage du panier
function updateCartVisibility() {
    const orderTotal = parseFloat(document.getElementById('order-total').textContent.replace(',', '.'));
    const cartSection = document.querySelector('.cart-container');
    const emptyCartMessage = document.querySelector('#empty-section');

    // Si le total est 0 ou indéfini, on considère le panier vide
    if (orderTotal <= 0 || isNaN(orderTotal)) {
        cartSection.style.display = 'none';
        emptyCartMessage.style.display = 'block';
    } else {
        cartSection.style.display = 'block';
        emptyCartMessage.style.display = 'none';
    }
}
// Fonction pour vider le panier
function clearCart() {
    fetch('/api/vider_panier/', { 
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFTokenFromMeta(),
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Réinitialise le localStorage
                localStorage.removeItem('cart');
                const addInsurance = document.getElementById('add-insurance');
                addInsurance.checked = false;
                alert(data.message);
                const formattedZero = currentLanguage === 'en' ? '0.00' : '0,00';
                document.getElementById('order-total').textContent = formattedZero;
                document.getElementById('total-amount').textContent = formattedZero;
                updateCartVisibility();
                initCart();
                updateTextCartButton();
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
    fetch(`/api/remove_from_cart/${articleId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFTokenFromMeta(),
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                let cart = JSON.parse(localStorage.getItem('cart')) || [];                
                cart = cart.filter(item => parseInt(item.id) !== parseInt(articleId));
                localStorage.setItem('cart', JSON.stringify(cart));
                const addInsurance = document.getElementById('add-insurance');
                let orderTotal = parseFloat(document.getElementById('order-total').textContent.replace(',', '.'));
                const priceArticle = parseFloat(data.article.prix.toFixed(2));
                orderTotal -= priceArticle;
                // Formater selon la langue
                const formattedTotal = currentLanguage === 'en' ? 
                    orderTotal.toFixed(2) : 
                    orderTotal.toFixed(2).replace('.', ',');
                document.getElementById('order-total').textContent = formattedTotal;
                if (orderTotal<25) {
                    addInsurance.checked = false;
                }
                updateInsurance();
                updateTotal();
                updateTextCartButton();
                alert(data.message);
                
            } else {
                alert("Erreur lors de la suppression de l'article.");
            }
        
        }).finally(()=>{
            displayCart();
            updateCartVisibility();
        });
}

let currentImageIndex = 0; // Index de l'image actuelle
let images = []; // Tableau pour stocker les images


// Fonction pour afficher les images d'un article avec le nom de l'article
function displayProductImages(articleId) {
    fetch(`/api/get_product_images/${articleId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json()
        })
        .then(data => {
            document.getElementById('nom-article').textContent = data.nom;

            const descriptionEl = document.getElementById('description-article');
            if (data.description) {
                descriptionEl.textContent = data.description;
            } else {
                descriptionEl.textContent =
                    currentLanguage === 'en'
                        ? 'No description available'
                        : 'Aucune description disponible';
            }
            const price = Number(data.prix);
            const discount = Number(data.discount || 0);
            const priceEl = document.getElementById('prix-article')
            const newPriceEl = document.getElementById('new_price');
            const newPriceH3El = document.getElementById('new_price_h3')
            
            
            priceEl.textContent = price.toFixed(2).replace('.', ',') + ' €';

            const promoWidget = document.getElementById('promo-widget');

            if (discount > 0) {
                promoWidget.style.display = "block";
                newPriceH3El.style.display = "INLINE"
                const newPrice = price - discount;
                
                priceEl.style.textDecoration = "line-through";
                priceEl.style.textDecorationThickness = "3px";
                priceEl.style.textDecorationColor = "#da0410"
                newPriceEl.textContent = newPrice.toFixed(2).replace('.', ',') + ' €';
            } else {
                priceEl.style.textDecoration = "none"
                newPriceEl.textContent = "";
                promoWidget.style.display = "none";
                newPriceH3El.style.display = "none"
            }

            // --- Bouton panier ---
            const addToCartButton = document.getElementById('id_add_to_cart_button');
            if (addToCartButton) {
                if (
                    window.location.pathname.includes('panier') ||
                    window.location.pathname.includes('cart') ||
                    data.en_attente_dans_panier ||
                    data.sur_commande
                ) {
                    addToCartButton.style.display = 'none';
                } else {
                    addToCartButton.style.display = 'block';
                    addToCartButton.style.width = "fit-content"
                    addToCartButton.dataset.productId = articleId;
                }
            }

            // --- Images ---
            images = data.images || [];
            currentImageIndex = 0;

            if (images.length > 0) {
                document.getElementById('current-image').src = images[0];
                document.getElementById('zoomImage').src = images[0];
            }

            // --- Modal ---
            document.getElementById('overlay').style.display = 'block';
            document.getElementById('modal').style.display = 'block';
        })
        .catch(error => {
            console.error('Fetch error:', error);
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
    document.getElementById('current-image').src = images[currentImageIndex]; // Mettre à jour l'image affichée
    document.getElementById('zoomImage').src = images[currentImageIndex]; // Mettre à jour l'image affichée dans le zoom
}

// Fonction pour fermer la modale
function closeModal() {
    const modal = document.getElementById('modal');
    const overlay = document.getElementById('overlay');
    overlay.style.display = 'none'; // Masque l'overlay
    modal.style.display = 'none';
}

// Fonction pour mettre à jour les frais de port
function updateShippingCost() {
    const currentLang = localStorage.getItem('language') || 'fr';
    const shippingOption = document.getElementById('add-shipping');
    const shippingCostSpan = document.getElementById('shipping-cost');
    if (shippingOption.checked) {
        const shippingCost = 10;
        const formattedShippingCost = currentLang === 'en'
        ? shippingCost.toFixed(2)
        : shippingCost.toFixed(2).replace('.', ',');
        shippingCostSpan.textContent = formattedShippingCost;
    } else {
        const shippingCost = 5;
        const formattedShippingCost = currentLang === 'en'
        ? shippingCost.toFixed(2)
        : shippingCost.toFixed(2).replace('.', ',');
        shippingCostSpan.textContent = formattedShippingCost;
    }
}
// Fonction pour mettre à jour l'assurance

function updateInsurance() {
    const orderTotalElement = document.getElementById('order-total');
    
    if (!orderTotalElement) {
        return;
    }
    
    const orderTotal = parseFloat(orderTotalElement.textContent.replace(',', '.'));    
    const insuranceOption = document.getElementById('insurance-option'); // Checkbox assurance optionnelle
    const mandatoryInsurance = document.getElementById('mandatory-insurance'); // Assurance obligatoire
    const insuranceCostSpan = document.getElementById('insurance-cost'); // Prix assurance optionnelle
    const mandatoryInsuranceCostSpan = document.getElementById('mandatory-insurance-cost'); // Prix assurance obligatoire
    const insurance25Euros = document.getElementById('insurance_25_euros'); // Message pour 25€ d'assurance incluse
    const insurance25Euros2 = document.getElementById('insurance_25_euros_2'); // Message pour 25€ d'assurance incluse
    const insurance = document.getElementById('insurance');
    const upTo500 = document.getElementById('mandatory_insurance_4');
    const insurance_info = document.getElementById('insurance_info');

    // Cacher toutes les options par défaut
    insuranceOption.classList.add('hidden');
    mandatoryInsurance.classList.add('hidden');
    insurance25Euros.classList.remove('hidden');
    insurance25Euros2.classList.remove('hidden');
    insurance.classList.remove('hidden');
    upTo500.classList.add('hidden');
    insuranceCostSpan.textContent = "0,00";
    mandatoryInsuranceCostSpan.textContent = "0,00";
    insurance_info.classList.add('hidden');

    // Fonction helper pour formater les nombres selon la langue
    const formatNumber = (num) => currentLanguage === 'en' ? 
    num.toFixed(2) : 
    num.toFixed(2).replace('.', ',');

    // 1. Gestion de l'assurance optionnelle entre 25 € et 50 €
    if (orderTotal > 25 && orderTotal <= 50) {
        insuranceOption.classList.remove('hidden'); // Afficher l'option d'assurance
        insurance.classList.add('hidden');
        if (insuranceOption.checked){
        insuranceCostSpan.textContent = formatNumber(2); // Coût fixe pour cette tranche
        }
    }

    // 2. Gestion de l'assurance obligatoire au-delà de 50 €
    if (orderTotal > 50) {
        insurance25Euros.classList.add('hidden');
        insurance25Euros2.classList.add('hidden');
        mandatoryInsurance.classList.remove('hidden');
        insurance_info.classList.remove('hidden');

        // Définir le coût de l'assurance obligatoire en fonction du total
        let insuranceAmount = 3.5;
        if (orderTotal > 500) {
            upTo500.classList.remove('hidden');
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
    const currentLang = localStorage.getItem('language') || 'fr';
    const orderTotalElement = document.getElementById('order-total');
    const insuranceCostElement = document.getElementById('insurance-cost');
    const totalAmountElement = document.getElementById('total-amount');
    
    if (!orderTotalElement || !insuranceCostElement || !totalAmountElement) {
        return;
    }
    
    const orderTotal = parseFloat(orderTotalElement.textContent.replace(',', '.'));
    const insuranceCost = parseFloat(insuranceCostElement.textContent.replace(',', '.')) || 0;
    
    
    const addInsurance = document.getElementById('add-insurance')?.checked || false;
    const addShipping = document.getElementById('add-shipping')?.checked || false;
    let totalAmount = orderTotal + 5.00 + insuranceCost;
    
    if (addInsurance && orderTotal > 25 && orderTotal <= 50) {
        totalAmount += 2.00;
    }
    if (addShipping) {
        totalAmount += 5.00;
    }
    const formattedTotal = currentLang === 'en'
        ? totalAmount.toFixed(2)
        : totalAmount.toFixed(2).replace('.', ',');
    
    totalAmountElement.textContent = formattedTotal;
}

// Fonction pour gérer le checkout
function handleCheckout() {
    const acceptCGV = document.getElementById('accept-cgv').checked;
    const addInsurance = document.getElementById('add-insurance').checked;
    const addShipping = document.getElementById('add-shipping').checked;
    const errorMessage = document.getElementById('error-message');
    let orderTotal = document.getElementById('total-amount').textContent;
    if (currentLanguage == 'fr'){
        orderTotal = orderTotal.replace(',', '.');
    }
    if (!acceptCGV) {
      errorMessage.classList.remove('hidden');
      return;
    }

    errorMessage.classList.add('hidden');

    // Récupérer l'UUID du panier depuis le localStorage
    const cart_uuid = localStorage.getItem('cart_uuid');


    if (!cart_uuid) {
        console.error("L'UUID du panier est introuvable.");
        return;
    }
    // Redirige vers Stripe avec le montant total
    window.location.href = `/api/checkout/?front_total=${orderTotal}&cart_uuid=${cart_uuid}&insurance=${addInsurance ? 1 : 0}&shipping=${addShipping ? 1 : 0}&acceptCGV=${acceptCGV ? 1 : 0}`;
  }
// débug
  function debugElements() {
    console.log("🔍 Debug des éléments DOM :");
    console.log("order-total :", document.getElementById('order-total'));
    console.log("insurance-cost :", document.getElementById('insurance-cost'));
    console.log("add-insurance :", document.getElementById('add-insurance'));
    console.log("total-amount :", document.getElementById('total-amount'));
}

function scrollToProducts() {
    const productsSection = document.getElementById('products-section');
    const offsetTop = productsSection.offsetTop - 62.5;
    if (productsSection) {
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

// Sortir les evenement onclick
if (document.getElementById("contact_link")) {
    document.getElementById("contact_link").addEventListener("click", function() {
        displayContact();
    });
}

if (document.getElementById("close-btn")) {
    document.getElementById("close-btn").addEventListener("click", function() {
        hideContact();
    });
}

if (document.getElementById("footer_contact")) {
    document.getElementById("footer_contact").addEventListener("click", function() {
        displayContact();
    });
}

if (document.getElementById("menu_button")) {
    document.getElementById("menu_button").addEventListener("click", function() {
        toggleMenu();
    });
}



if (document.getElementById("contact_button")) {
    document.getElementById("contact_button").addEventListener("click", function() {
        displayContact();
    });
}

if (document.getElementById("clear_cart")) {
    document.getElementById("clear_cart").addEventListener("click", function() {
        clearCart();
    });
}

if (document.getElementById("add-insurance")) {
    document.getElementById("add-insurance").addEventListener("change", function() {
        updateTotal();
    });
}
if (document.getElementById("add-shipping")) {
    document.getElementById("add-shipping").addEventListener("change", function() {
        updateShippingCost();
        updateTotal();
    });
}

if (document.getElementById("checkout")) {
    document.getElementById("checkout").addEventListener("click", function() {
        handleCheckout();
    });
}

if (document.getElementById("close-button")) {
    document.getElementById("close-button").addEventListener("click", function() {
        closeModal();
    });
}

if (document.getElementById("prev-button")) {
    document.getElementById("prev-button").addEventListener("click", function() {
        changeImage(-1);
    });
}

if (document.getElementById("next-button")) {
    document.getElementById("next-button").addEventListener("click", function() {
        changeImage(1);
    });
}

if (document.getElementById("clean_filter")) {
    document.getElementById("clean_filter").addEventListener("click", function() {
        cleanFilter();
    });
}

document.addEventListener("click", function(event) {
    if (event.target && event.target.matches(".add_to_cart_button")) {
        const articleId = event.target.getAttribute('data-product-id');
        if (!articleId) return;
        addToCart(articleId);
    }
});

document.addEventListener('languageChanged', function() {
    if(window.location.pathname.includes('panier') || window.location.pathname.includes('cart')){
        updateInsurance();
        updateTotal();
    }
});

if (document.getElementById("see_products_button")) {
    document.getElementById("see_products_button").addEventListener("click", function() {
        scrollToProducts();
    });
}

// Zoom dans modal
if (document.getElementById("imageContainer")) {
document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('imageContainer');
    const baseImage = document.getElementById('current-image');
    const loupe = document.getElementById('loupe');
    const zoomImage = document.getElementById('zoomImage');
    const zoom = 2; // facteur de zoom
  
    container.addEventListener('mousemove', function (e) {
      const rect = baseImage.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
  
      if (x < 0 || y < 0 || x > rect.width || y > rect.height || window.innerWidth < 768) {
        loupe.style.display = 'none';
        return;
      }
      loupe.style.display = 'block';
  
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
  
    container.addEventListener('mouseleave', function () {
      loupe.style.display = 'none';
    });
  });
}