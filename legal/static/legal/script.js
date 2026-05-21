const API_BASE_URL = "/api/legal";

async function updateLegalDocuments(lang) {
  const documentTypes = [
    "terms",
    "cookies",
    "legal_mentions",
    "privacy_policy",
  ];

  const promises = documentTypes.map((docType) => {
    const element = document.getElementById(`${docType}_content`);
    if (!element) return Promise.resolve();
    return getDocumentContent(docType, lang).then((content) => {
      if (content) element.innerHTML = content;
    });
  });

  await Promise.all(promises);
}

async function getDocumentContent(documentType, lang) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/get_document_content/${documentType}/${lang}/`,
    );
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    return await response.text();
  } catch (error) {
    console.error("Error fetching document content:", error);
    return null;
  }
}

document.addEventListener("languageChanged", (event) => {
  updateLegalDocuments(event.detail.lang);
});
