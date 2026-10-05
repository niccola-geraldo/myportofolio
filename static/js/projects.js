const projectsApp = document.getElementById("projects-app");

if (projectsApp) {
    const searchForm = document.getElementById("project-search-form");
    const searchInput = document.getElementById("search-input");
    const loadingState = document.getElementById("projects-loading");
    const errorState = document.getElementById("projects-error");
    const emptyState = document.getElementById("projects-empty");
    const grid = document.getElementById("project-grid");
    const superuser = projectsApp.dataset.isSuperuser === "true";
    const editor = projectsApp.dataset.isEditor === "true";
    const { element, csrfToken, csrfField, endpointFor } =
        globalThis.portfolioUtils;
    let searchDebounceTimer;
    let activeRequest;
    let requestSequence = 0;

    function safeHttpUrl(value) {
        if (!value) return null;
        try {
            const url = new URL(value, window.location.href);
            return ["http:", "https:"].includes(url.protocol) ? url.href : null;
        } catch {
            return null;
        }
    }

    function buildStarForm(project) {
        const form = element("form", "star-form");
        form.method = "post";
        form.action = endpointFor(projectsApp.dataset.starUrlTemplate, project.pk) ?? "";
        form.append(csrfField());

        const button = element(
            "button",
            `button button-star${project.fields.is_starred ? " is-starred" : ""}`,
        );
        button.type = "submit";
        button.title = project.fields.starred_by_names
            ? `Dibintangi oleh ${project.fields.starred_by_names}`
            : "Jadilah yang pertama memberi star";

        const star = element("span", "", "★");
        star.setAttribute("aria-hidden", "true");
        button.append(
            star,
            document.createTextNode(project.fields.is_starred ? " Unstar " : " Star "),
        );
        button.append(element("span", "star-count", project.fields.star_count));
        form.append(button);
        return form;
    }

    function buildDeleteModal(project) {
        const id = `delete-project-${project.pk}`;
        const trigger = element("button", "button button-danger", "Hapus Proyek");
        trigger.type = "button";
        trigger.setAttribute("popovertarget", id);
        trigger.setAttribute("aria-label", `Hapus ${project.fields.title}`);
        trigger.title = "Hapus proyek";

        const modal = element("div", "project-delete-modal");
        modal.id = id;
        modal.setAttribute("popover", "auto");
        modal.setAttribute("role", "dialog");
        modal.setAttribute("aria-modal", "true");
        modal.setAttribute("aria-labelledby", `${id}-title`);

        const backdrop = element("button", "project-delete-modal__backdrop");
        backdrop.type = "button";
        backdrop.setAttribute("popovertarget", id);
        backdrop.setAttribute("popovertargetaction", "hide");
        backdrop.setAttribute("aria-label", "Tutup konfirmasi hapus");

        const content = element("div", "project-delete-modal__content");
        const close = element("button", "project-delete-modal__close", "×");
        close.type = "button";
        close.setAttribute("popovertarget", id);
        close.setAttribute("popovertargetaction", "hide");
        close.setAttribute("aria-label", "Tutup konfirmasi hapus");

        const heading = element("h2", "", "Hapus Proyek?");
        heading.id = `${id}-title`;
        const prompt = element("p", "", "Apakah Anda yakin ingin menghapus ");
        prompt.append(element("strong", "", project.fields.title), "?");

        const actions = element("div", "project-delete-modal__actions");
        const cancel = element("button", "button button-secondary", "Batal");
        cancel.type = "button";
        cancel.setAttribute("popovertarget", id);
        cancel.setAttribute("popovertargetaction", "hide");

        const form = element("form");
        form.method = "post";
        form.action = endpointFor(projectsApp.dataset.deleteUrlTemplate, project.pk) ?? "";
        form.append(csrfField());
        const submit = element("button", "button button-danger", "Ya, Hapus");
        submit.type = "submit";
        form.append(submit);

        actions.append(cancel, form);
        content.append(close, heading, prompt, actions);
        modal.append(backdrop, content);
        return { trigger, modal };
    }

    function buildProjectCard(project) {
        const fields = project.fields;
        const article = element("article", "experience-card");
        const imageUrl = safeHttpUrl(fields.project_image_url);
        if (imageUrl) {
            const image = element("img", "project-image");
            image.src = imageUrl;
            image.alt = `Gambar ${fields.title}`;
            article.append(image);
        }

        article.append(
            element("h2", "", fields.title),
            element("span", "experience-category", fields.tech_stack),
            element("p", "experience-description", fields.description),
        );

        const cardActions = element("div", "project-card-actions");
        const actions = element("div", "project-actions");
        const projectUrl = safeHttpUrl(fields.project_url);
        if (projectUrl) {
            const link = element("a", "button", "Lihat Project");
            link.href = projectUrl;
            actions.append(link);
        }
        actions.append(buildStarForm(project));

        if (editor || superuser) {
            const editUrl = endpointFor(projectsApp.dataset.updateUrlTemplate, project.pk);
            if (editUrl) {
                const edit = element("a", "button button-secondary", "Edit");
                edit.href = editUrl;
                actions.append(edit);
            }
        }

        if (superuser) {
            const deletion = buildDeleteModal(project);
            actions.append(deletion.trigger);
            cardActions.append(actions, deletion.modal);
        } else {
            cardActions.append(actions);
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

    async function fetchProjects(query = "") {
        activeRequest?.abort();
        activeRequest = new AbortController();
        const sequence = ++requestSequence;
        displayState("loading");

        const url = new URL(projectsApp.dataset.jsonUrl, window.location.href);
        if (query) url.searchParams.set("title", query);

        try {
            const response = await fetch(url, {
                headers: { Accept: "application/json" },
                signal: activeRequest.signal,
            });
            if (!response.ok) throw new Error(`Request failed (${response.status})`);

            const projects = await response.json();
            if (!Array.isArray(projects)) throw new Error("Invalid project data");
            if (sequence !== requestSequence) return;

            grid.replaceChildren();
            if (projects.length === 0) {
                emptyState.textContent = query
                    ? "Tidak ada proyek dengan nama tersebut."
                    : "Belum ada proyek yang ditambahkan.";
                displayState("empty");
                return;
            }

            for (const project of projects) {
                grid.append(buildProjectCard(project));
            }
            displayState("grid");
        } catch (error) {
            if (error.name === "AbortError" || sequence !== requestSequence) return;
            console.error("Error loading projects:", error);
            displayState("error");
        }
    }

    function searchProjects() {
        window.clearTimeout(searchDebounceTimer);
        fetchProjects(searchInput.value.trim());
    }

    searchInput.addEventListener("input", () => {
        window.clearTimeout(searchDebounceTimer);
        searchDebounceTimer = window.setTimeout(
            () => fetchProjects(searchInput.value.trim()),
            300,
        );
    });

    searchForm.addEventListener("submit", (event) => {
        event.preventDefault();
        searchProjects();
    });

    document
        .getElementById("projects-retry")
        .addEventListener("click", () => fetchProjects(searchInput.value.trim()));

    const projectForm = document.getElementById("project-form");
    if (projectForm) {
        projectForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const submitButton = projectForm.querySelector("button[type='submit']");
            submitButton.disabled = true;

            try {
                const response = await fetch(projectForm.action, {
                    method: "POST",
                    headers: { "X-CSRFToken": csrfToken(), Accept: "application/json" },
                    body: new FormData(projectForm),
                });
                const result = await response.json().catch(() => ({}));

                if (response.ok) {
                    projectForm.reset();
                    document.getElementById("add-project-modal").hidePopover();
                    globalThis.showToast("Berhasil", result.message, "success");
                    fetchProjects(searchInput.value.trim());
                    return;
                }

                const errors = result.errors
                    ? Object.values(result.errors).flatMap((items) =>
                          items.map((item) => item.message),
                      )
                    : [result.message ?? `Terjadi kesalahan (status ${response.status}).`];
                globalThis.showToast(
                    "Gagal menambahkan proyek",
                    errors.join(" "),
                    "error",
                );
            } catch (error) {
                console.error("Error adding project:", error);
                globalThis.showToast(
                    "Gagal menambahkan proyek",
                    "Tidak dapat terhubung ke server. Silakan coba lagi.",
                    "error",
                );
            } finally {
                submitButton.disabled = false;
            }
        });
    }

    fetchProjects(searchInput.value.trim());
}
