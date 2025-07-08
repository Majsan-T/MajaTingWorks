document.addEventListener("DOMContentLoaded", function () {
    const editors = document.querySelectorAll(".quill-editor");
    const quills = [];

    // Deklarera global filstorleksgräns
    const MAX_FILE_SIZE_MB = 10;
    const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

    editors.forEach(function (editorDiv) {
        const inputSelector = editorDiv.getAttribute("data-input");
        const hiddenInput = document.querySelector(inputSelector);

        if (!hiddenInput) {
            console.warn(`Hidden input not found for editor: ${editorDiv.id || editorDiv.className}. Skipping initialization.`);
            return;
        }

        console.log("Found hidden input:", hiddenInput);
        console.log("Hidden input name attribute:", hiddenInput.name);

        const quill = new Quill(editorDiv, {
            theme: "snow",
            placeholder: "Skriv här...",
            modules: {
                toolbar: {
                    container: [
                        ["bold", "italic", "underline"],
                        [{ list: "bullet" }],
                        ["link", "image", "code"],
                        ["clean"]
                    ],
                    handlers: {
                        image: function () {
                            const input = document.createElement("input");
                            input.setAttribute("type", "file");
                            input.setAttribute("accept", "image/*");
                            input.click();

                            input.onchange = async () => {
                                const file = input.files[0];
                                if (!file) return;

                                if (file.size > MAX_FILE_SIZE_BYTES) {
                                    alert(`Bilden är för stor! Maxstorlek är ${MAX_FILE_SIZE_MB} MB.`);
                                    return;
                                }

                                const formData = new FormData();
                                formData.append("image", file);

                                try {
                                    const uploadUrl = editorDiv.getAttribute("data-upload") || "/blog/upload";
                                    const response = await fetch(uploadUrl, {
                                        method: "POST",
                                        body: formData
                                    });

                                    const data = await response.json();

                                    if (data.url) {
                                        const range = this.quill.getSelection();
                                        if (range) {
                                            this.quill.insertEmbed(range.index, "image", data.url);
                                        } else {
                                            // Om inget område är markerat, lägg till bilden sist i dokumentet
                                            this.quill.insertEmbed(this.quill.getLength(), "image", data.url);
                                        }
                                    } else {
                                        alert("Fel vid uppladdning: " + (data.error || "okänt fel"));
                                    }
                                } catch (error) {
                                    console.error("Uppladdningsfel:", error);
                                    alert("Något gick fel vid uppladdningen.");
                                }
                            };
                        }
                    }
                }
            }
        });

        // Hantera initialt innehåll
        let initialContent = hiddenInput.value;
        if (initialContent === "None") {
            initialContent = "";
        }

        if (initialContent) {
            // ⚠️ Här sker en "dangerous" inmatning – se till att detta är sanerat server-side
            const tempDiv = document.createElement("div");
            tempDiv.innerHTML = initialContent;
            initialContent = tempDiv.innerHTML;
        }

        if (initialContent.trim() !== "") {
            quill.clipboard.dangerouslyPasteHTML(initialContent);
        } else {
            quill.setText('');
        }

        // Sätt Quill-innehåll på hiddenInput vid form.submit
        const form = hiddenInput.closest("form");
        if (form) {
            form.addEventListener("submit", function () {
                console.log("Form submit event triggered!");
                const quillContent = quill.root.innerHTML.trim();
                console.log("Quill editor HTML content:", quillContent);

                hiddenInput.value = (quillContent === "<p><br></p>" || quillContent === "<p></p>") ? "" : quillContent;

                console.log("Hidden input value set to:", hiddenInput.value);
                console.log("Form will now submit.");
            });
        }

        quills.push(quill);
    });
});
