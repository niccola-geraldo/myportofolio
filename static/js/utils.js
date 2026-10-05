(function () {
    const uuidPlaceholder = "00000000-0000-0000-0000-000000000000";
    const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

    function element(tagName, className, text) {
        const node = document.createElement(tagName);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = String(text ?? "");
        return node;
    }

    function csrfToken() {
        const input = document.querySelector(
            "#csrf-token-form input[name='csrfmiddlewaretoken']",
        );
        return input?.value ?? "";
    }

    function csrfField() {
        const input = element("input");
        input.type = "hidden";
        input.name = "csrfmiddlewaretoken";
        input.value = csrfToken();
        return input;
    }

    function endpointFor(template, id) {
        if (!uuidPattern.test(String(id))) return null;
        return template.replace(uuidPlaceholder, encodeURIComponent(id));
    }

    globalThis.portfolioUtils = { element, csrfToken, csrfField, endpointFor };
})();
