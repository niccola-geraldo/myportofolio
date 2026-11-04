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
    const authenticated = projectsApp.dataset.isAuthenticated === "true";
    const { element, csrfToken, endpointFor } = globalThis.portfolioUtils;
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

    function apiErrorMessage(data, status) {
        const messages = Object.values(data ?? {})
            .flat()
            .filter((value) => typeof value === "string");
        return messages.join(" ") || `Terjadi kesalahan (status ${status}).`;
    }

    async function writeProject(url, method, payload) {
        const response = await fetch(url, {
            method,
            headers: {
                Accept: "application/json",
                ...(payload === undefined
                    ? {}
                    : { "Content-Type": "application/json" }),
                "X-CSRFToken": csrfToken(),
            },
            body: payload === undefined ? undefined : JSON.stringify(payload),
        });

        if (response.status === 204) return null;

        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(apiErrorMessage(data, response.status));
        return data;
    }

    function buildStar(project) {
        if (!authenticated) {
            const link = element(
                "a",
                "button",
                `Login untuk star (${project.star_count})`,
            );
            link.href = projectsApp.dataset.loginUrl;
            return link;
        }

        const button = element(
            "button",
            `button button-star${project.is_starred ? " is-starred" : ""}`,
        );
        button.type = "button";
        button.dataset.action = "star";
        button.dataset.id = project.id;
        button.title = project.starred_by_names
            ? `Dibintangi oleh ${project.starred_by_names}`
            : "Jadilah yang pertama memberi star";

        const star = element("span", "", "★");
        star.setAttribute("aria-hidden", "true");
        button.append(
            star,
            document.createTextNode(project.is_starred ? " Unstar " : " Star "),
        );
        button.append(element("span", "star-count", project.star_count));
        return button;
    }

    function buildDeleteModal(project) {
        const id = `delete-project-${project.id}`;
        const trigger = element("button", "button button-danger", "Hapus Proyek");
        trigger.type = "button";
        trigger.setAttribute("popovertarget", id);
        trigger.setAttribute("aria-label", `Hapus ${project.title}`);
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
        prompt.append(element("strong", "", project.title), "?");

        const actions = element("div", "project-delete-modal__actions");
        const cancel = element("button", "button button-secondary", "Batal");
        cancel.type = "button";
        cancel.setAttribute("popovertarget", id);
        cancel.setAttribute("popovertargetaction", "hide");

        const confirm = element("button", "button button-danger", "Ya, Hapus");
        confirm.type = "button";
        confirm.dataset.action = "delete";
        confirm.dataset.id = project.id;

        actions.append(cancel, confirm);
        content.append(close, heading, prompt, actions);
        modal.append(backdrop, content);
        return { trigger, modal };
    }

    function buildProjectCard(project) {
        const article = element("article", "experience-card");
        const imageUrl = safeHttpUrl(project.project_image_url);
        if (imageUrl) {
            const image = element("img", "project-image");
            image.src = imageUrl;
            image.alt = `Gambar ${project.title}`;
            article.append(image);
        }

        article.append(
            element("h2", "", project.title),
            element("span", "experience-category", project.tech_stack),
            element("p", "experience-description", project.description),
        );

        const cardActions = element("div", "project-card-actions");
        const actions = element("div", "project-actions");
        const projectUrl = safeHttpUrl(project.project_url);
        if (projectUrl) {
            const link = element("a", "button", "Lihat Project");
            link.href = projectUrl;
            actions.append(link);
        }
        actions.append(buildStar(project));

        if (editor || superuser) {
            const editUrl = endpointFor(projectsApp.dataset.updateUrlTemplate, project.id);
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

        const url = new URL(projectsApp.dataset.listUrl, window.location.href);
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
                const fields = new FormData(projectForm);
                const payload = Object.fromEntries(
                    [
                        "title",
                        "description",
                        "tech_stack",
                        "project_url",
                        "project_image_url",
                    ].map((name) => [name, fields.get(name) ?? ""]),
                );

                await writeProject(projectsApp.dataset.listUrl, "POST", payload);
                projectForm.reset();
                document.getElementById("add-project-modal").hidePopover();
                globalThis.showToast("Berhasil", "Proyek berhasil ditambahkan.", "success");
                await fetchProjects(searchInput.value.trim());
            } catch (error) {
                console.error("Error adding project:", error);
                globalThis.showToast("Gagal menambahkan proyek", error.message, "error");
            } finally {
                submitButton.disabled = false;
            }
        });
    }

    grid.addEventListener("click", async (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button || button.disabled) return;

        const action = button.dataset.action;
        const template =
            action === "star"
                ? projectsApp.dataset.starUrlTemplate
                : projectsApp.dataset.detailUrlTemplate;
        const url = endpointFor(template, button.dataset.id);
        if (!url) return;

        button.disabled = true;
        try {
            await writeProject(url, action === "star" ? "POST" : "DELETE");
            if (action === "delete") button.closest("[popover]")?.hidePopover();
            globalThis.showToast(
                "Berhasil",
                action === "star"
                    ? "Status star berhasil diperbarui."
                    : "Proyek berhasil dihapus.",
                "success",
            );
            await fetchProjects(searchInput.value.trim());
        } catch (error) {
            console.error("Error updating project:", error);
            globalThis.showToast("Permintaan gagal", error.message, "error");
        } finally {
            button.disabled = false;
        }
    });

    fetchProjects(searchInput.value.trim());
}
