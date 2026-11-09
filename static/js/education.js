const educationApp = document.getElementById("education-app");

if (educationApp) {
    const { element, csrfToken, endpointFor } = globalThis.portfolioUtils;
    const searchForm = document.getElementById("education-search-form");
    const searchInput = document.getElementById("education-search-input");
    const loadingState = document.getElementById("education-loading");
    const errorState = document.getElementById("education-error");
    const emptyState = document.getElementById("education-empty");
    const grid = document.getElementById("education-grid");
    const educationForm = document.getElementById("education-form");
    const formModal = document.getElementById("education-form-modal");
    const formTitle = document.getElementById("education-form-modal-title");
    const submitButton = educationForm?.querySelector("button[type='submit']");
    const superuser = educationApp.dataset.isSuperuser === "true";
    const editor = educationApp.dataset.isEditor === "true";
    const authenticated = educationApp.dataset.isAuthenticated === "true";
    const formFields = [
        "institution", "degree", "major", "description", "start_year", "end_year", "gpa",
    ];
    const pendingCardActions = new Set();
    let searchDebounceTimer;
    let activeRequest;
    let requestSequence = 0;
    let editingUrl;
    let originalFields;

    async function writeEducation(url, method, payload) {
        const headers = { Accept: "application/json", "X-CSRFToken": csrfToken() };
        if (payload !== undefined) headers["Content-Type"] = "application/json";

        const response = await fetch(url, {
            method,
            headers,
            body: payload === undefined ? undefined : JSON.stringify(payload),
        }).catch(() => {
            throw new Error("Tidak dapat terhubung ke server. Silakan coba lagi.");
        });
        if (response.ok) return;

        const data = await response.json().catch(() => ({}));
        const messages = Object.values(data ?? {})
            .flat()
            .filter((value) => typeof value === "string");
        throw new Error(messages.join(" ") || `Terjadi kesalahan (status ${response.status}).`);
    }

    function readFormFields() {
        return Object.fromEntries(formFields.map((name) => {
            const value = educationForm.elements.namedItem(name).value;
            const nullable = name === "end_year" || name === "gpa";
            return [name, nullable && value === "" ? null : value];
        }));
    }

    function prepareForm(event, education) {
        const detailUrl = education
            ? endpointFor(educationApp.dataset.detailUrlTemplate, education.id)
            : null;
        if (submitButton.disabled || (education && !detailUrl)) {
            event.preventDefault();
            return;
        }

        editingUrl = detailUrl;
        educationForm.reset();
        if (education) {
            for (const name of formFields) {
                educationForm.elements.namedItem(name).value = education[name] ?? "";
            }
        }
        originalFields = editingUrl ? readFormFields() : null;
        formTitle.textContent = editingUrl ? "Ubah Pendidikan" : "Tambah Pendidikan Baru";
        submitButton.textContent = editingUrl ? "Simpan Perubahan" : "Tambah Pendidikan";
    }

    async function runCardAction(button, education, action) {
        if (pendingCardActions.has(education.id)) return;

        const isStar = action === "star";
        const template = isStar
            ? educationApp.dataset.starUrlTemplate
            : educationApp.dataset.detailUrlTemplate;
        const url = endpointFor(template, education.id);
        if (!url) return;

        pendingCardActions.add(education.id);
        button.disabled = true;
        try {
            await writeEducation(url, isStar ? "POST" : "DELETE");
            if (!isStar) button.closest("[popover]:popover-open")?.hidePopover();
            globalThis.showToast(
                "Berhasil",
                isStar ? "Status star berhasil diperbarui." : "Pendidikan berhasil dihapus.",
                "success",
            );
            searchEducation();
        } catch (error) {
            globalThis.showToast("Permintaan gagal", error.message, "error");
        } finally {
            button.disabled = false;
            pendingCardActions.delete(education.id);
        }
    }

    function buildStar(education) {
        if (!authenticated) {
            return element("span", "", `Star: ${education.star_count}`);
        }

        const button = element(
            "button",
            `button button-star${education.is_starred ? " is-starred" : ""}`,
            education.is_starred ? "★ Unstar" : "☆ Star",
        );
        button.type = "button";
        button.setAttribute("aria-pressed", String(education.is_starred));
        button.setAttribute("aria-label", `Star ${education.institution} (${education.star_count})`);
        button.append(element("span", "star-count", education.star_count));
        button.addEventListener("click", () => runCardAction(button, education, "star"));
        return button;
    }

    function buildDeleteModal(education) {
        const id = `delete-education-${education.id}`;
        const trigger = element("button", "button button-danger", "Hapus");
        trigger.type = "button";
        trigger.setAttribute("popovertarget", id);
        trigger.setAttribute("aria-label", `Hapus ${education.institution}`);
        trigger.title = "Hapus pendidikan";

        const modal = element("div", "education-delete-modal");
        modal.id = id;
        modal.setAttribute("popover", "auto");
        modal.setAttribute("role", "dialog");
        modal.setAttribute("aria-modal", "true");
        modal.setAttribute("aria-labelledby", `${id}-title`);

        const backdrop = element("button", "education-delete-modal__backdrop");
        backdrop.type = "button";
        backdrop.setAttribute("popovertarget", id);
        backdrop.setAttribute("popovertargetaction", "hide");
        backdrop.setAttribute("aria-label", "Tutup konfirmasi hapus");

        const content = element("div", "education-delete-modal__content");
        const close = element("button", "education-delete-modal__close", "×");
        close.type = "button";
        close.setAttribute("popovertarget", id);
        close.setAttribute("popovertargetaction", "hide");
        close.setAttribute("aria-label", "Tutup konfirmasi hapus");

        const heading = element("h2", "", "Hapus Pendidikan?");
        heading.id = `${id}-title`;
        const prompt = element("p", "", "Apakah Anda yakin ingin menghapus ");
        prompt.append(element("strong", "", education.institution), "?");

        const actions = element("div", "education-delete-modal__actions");
        const cancel = element("button", "button button-secondary", "Batal");
        cancel.type = "button";
        cancel.setAttribute("popovertarget", id);
        cancel.setAttribute("popovertargetaction", "hide");

        const confirm = element("button", "button button-danger", "Ya, Hapus");
        confirm.type = "button";
        confirm.addEventListener("click", () => runCardAction(confirm, education, "delete"));

        actions.append(cancel, confirm);
        content.append(close, heading, prompt, actions);
        modal.append(backdrop, content);
        return { trigger, modal };
    }

    function buildEducationCard(education) {
        const article = element("article", "experience-card");

        article.append(
            element("span", "experience-category", education.degree_display),
            element("h2", "", education.institution),
        );

        const meta = element("p", "education-meta");
        meta.append(element("strong", "", education.major));
        article.append(meta);

        const years = element("p", "education-years");
        years.append(
            document.createTextNode(`${education.start_year} — `),
            education.is_ongoing ? "Sekarang" : String(education.end_year ?? ""),
        );
        article.append(
            years,
            element(
                "p",
                "education-status",
                education.is_ongoing ? "Ongoing" : "Selesai",
            ),
            element("p", "education-description", education.description),
        );

        if (education.gpa != null) {
            article.append(element("p", "education-gpa", `GPA: ${education.gpa}`));
        }

        const cardActions = element("div", "education-card-actions");
        const actions = element("div", "education-actions");
        actions.append(buildStar(education));
        cardActions.append(actions);
        if (editor || superuser) {
            const edit = element("button", "button button-secondary", "Edit");
            edit.type = "button";
            edit.setAttribute("popovertarget", formModal.id);
            edit.addEventListener("click", (event) => prepareForm(event, education));
            actions.append(edit);
        }
        if (superuser) {
            const deletion = buildDeleteModal(education);
            actions.append(deletion.trigger);
            cardActions.append(deletion.modal);
        }
        article.append(cardActions);

        return article;
    }

    function displayState(state) {
        loadingState.classList.toggle("hide", state !== "loading");
        errorState.classList.toggle("hide", state !== "error");
        emptyState.classList.toggle("hide", state !== "empty");
        grid.classList.toggle("hide", state !== "grid");
    }

    async function fetchEducation(query = "") {
        activeRequest?.abort();
        activeRequest = new AbortController();
        const sequence = ++requestSequence;
        displayState("loading");

        const url = new URL(educationApp.dataset.listUrl, window.location.href);
        if (query) url.searchParams.set("institution", query);

        try {
            const response = await fetch(url, {
                headers: { Accept: "application/json" },
                signal: activeRequest.signal,
            });
            if (!response.ok) throw new Error(`Request failed (${response.status})`);

            const educations = await response.json();
            if (!Array.isArray(educations)) throw new Error("Invalid education data");
            if (sequence !== requestSequence) return;

            grid.replaceChildren();
            if (educations.length === 0) {
                emptyState.textContent = query
                    ? "Tidak ada pendidikan dengan institusi tersebut."
                    : "Belum ada pendidikan yang ditambahkan.";
                displayState("empty");
                return;
            }

            for (const education of educations) {
                grid.append(buildEducationCard(education));
            }
            displayState("grid");
        } catch (error) {
            if (error.name === "AbortError" || sequence !== requestSequence) return;
            console.error("Error loading education:", error);
            displayState("error");
        }
    }

    function searchEducation() {
        window.clearTimeout(searchDebounceTimer);
        fetchEducation(searchInput.value.trim());
    }

    searchInput.addEventListener("input", () => {
        window.clearTimeout(searchDebounceTimer);
        searchDebounceTimer = window.setTimeout(
            () => fetchEducation(searchInput.value.trim()),
            300,
        );
    });

    searchForm.addEventListener("submit", (event) => {
        event.preventDefault();
        searchEducation();
    });

    document
        .getElementById("education-retry")
        .addEventListener("click", () => fetchEducation(searchInput.value.trim()));

    if (educationForm) {
        document.getElementById("education-add-button")?.addEventListener("click", prepareForm);
        educationForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (submitButton.disabled) return;

            const payload = readFormFields();
            const editing = Boolean(editingUrl);
            if (editing) {
                for (const name of formFields) {
                    if (payload[name] === originalFields[name]) delete payload[name];
                }
                if (Object.keys(payload).length === 0) {
                    formModal.hidePopover();
                    return;
                }
            }

            submitButton.disabled = true;
            educationForm.inert = true;

            try {
                await writeEducation(editingUrl ?? educationForm.action, editing ? "PATCH" : "POST", payload);
                educationForm.reset();
                if (formModal.matches(":popover-open")) formModal.hidePopover();
                globalThis.showToast(
                    "Berhasil",
                    editing ? "Data pendidikan berhasil diubah." : "Pendidikan berhasil ditambahkan.",
                    "success",
                );
                searchEducation();
            } catch (error) {
                globalThis.showToast("Gagal menyimpan pendidikan", error.message, "error");
            } finally {
                educationForm.inert = false;
                submitButton.disabled = false;
            }
        });
    }

    searchEducation();
}
