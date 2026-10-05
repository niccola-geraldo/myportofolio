const educationApp = document.getElementById("education-app");

if (educationApp) {
    const { element, csrfToken, csrfField, endpointFor } =
        globalThis.portfolioUtils;
    const searchForm = document.getElementById("education-search-form");
    const searchInput = document.getElementById("education-search-input");
    const loadingState = document.getElementById("education-loading");
    const errorState = document.getElementById("education-error");
    const emptyState = document.getElementById("education-empty");
    const grid = document.getElementById("education-grid");
    const superuser = educationApp.dataset.isSuperuser === "true";
    const editor = educationApp.dataset.isEditor === "true";
    let searchDebounceTimer;
    let activeRequest;
    let requestSequence = 0;

    function buildDeleteModal(education) {
        const id = `delete-education-${education.pk}`;
        const trigger = element("button", "button button-danger", "Hapus");
        trigger.type = "button";
        trigger.setAttribute("popovertarget", id);
        trigger.setAttribute("aria-label", `Hapus ${education.fields.institution}`);
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
        prompt.append(element("strong", "", education.fields.institution), "?");

        const actions = element("div", "education-delete-modal__actions");
        const cancel = element("button", "button button-secondary", "Batal");
        cancel.type = "button";
        cancel.setAttribute("popovertarget", id);
        cancel.setAttribute("popovertargetaction", "hide");

        const form = element("form");
        form.method = "post";
        form.action =
            endpointFor(educationApp.dataset.deleteUrlTemplate, education.pk) ?? "";
        form.append(csrfField());
        const submit = element("button", "button button-danger", "Ya, Hapus");
        submit.type = "submit";
        form.append(submit);

        actions.append(cancel, form);
        content.append(close, heading, prompt, actions);
        modal.append(backdrop, content);
        return { trigger, modal };
    }

    function buildEducationCard(education) {
        const fields = education.fields;
        const article = element("article", "experience-card");

        article.append(
            element("span", "experience-category", fields.degree_display),
            element("h2", "", fields.institution),
        );

        const meta = element("p", "education-meta");
        meta.append(element("strong", "", fields.major));
        article.append(meta);

        const years = element("p", "education-years");
        years.append(
            document.createTextNode(`${fields.start_year} — `),
            fields.is_ongoing ? "Sekarang" : String(fields.end_year ?? ""),
        );
        article.append(
            years,
            element(
                "p",
                "education-status",
                fields.is_ongoing ? "Ongoing" : "Selesai",
            ),
            element("p", "education-description", fields.description),
        );

        if (fields.gpa) {
            article.append(element("p", "education-gpa", `GPA: ${fields.gpa}`));
        }

        if (editor || superuser) {
            const cardActions = element("div", "education-card-actions");
            const actions = element("div", "education-actions");
            const editUrl = endpointFor(
                educationApp.dataset.updateUrlTemplate,
                education.pk,
            );
            if (editUrl) {
                const edit = element("a", "button button-secondary", "Edit");
                edit.href = editUrl;
                actions.append(edit);
            }

            if (superuser) {
                const deletion = buildDeleteModal(education);
                actions.append(deletion.trigger);
                cardActions.append(actions, deletion.modal);
            } else {
                cardActions.append(actions);
            }

            article.append(cardActions);
        }

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

        const url = new URL(educationApp.dataset.jsonUrl, window.location.href);
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

    const educationForm = document.getElementById("education-form");
    if (educationForm) {
        educationForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const submitButton = educationForm.querySelector("button[type='submit']");
            submitButton.disabled = true;

            try {
                const response = await fetch(educationForm.action, {
                    method: "POST",
                    headers: { "X-CSRFToken": csrfToken(), Accept: "application/json" },
                    body: new FormData(educationForm),
                });
                const result = await response.json().catch(() => ({}));

                if (response.ok) {
                    educationForm.reset();
                    document.getElementById("add-education-modal").hidePopover();
                    globalThis.showToast("Berhasil", result.message, "success");
                    fetchEducation(searchInput.value.trim());
                    return;
                }

                const errors = result.errors
                    ? Object.values(result.errors).flatMap((items) =>
                          items.map((item) => item.message),
                      )
                    : [result.message ?? `Terjadi kesalahan (status ${response.status}).`];
                globalThis.showToast(
                    "Gagal menambahkan pendidikan",
                    errors.join(" "),
                    "error",
                );
            } catch (error) {
                console.error("Error adding education:", error);
                globalThis.showToast(
                    "Gagal menambahkan pendidikan",
                    "Tidak dapat terhubung ke server. Silakan coba lagi.",
                    "error",
                );
            } finally {
                submitButton.disabled = false;
            }
        });
    }

    fetchEducation();
}
