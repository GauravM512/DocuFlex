const tools = document.querySelectorAll(".tool[data-endpoint]");

const setStatus = (form, text, isError = false) => {
  const status = form.querySelector(".status");
  status.textContent = text;
  status.style.color = isError ? "#d64545" : "";
};

const downloadBlob = async (response) => {
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^\"]+)"?/);
  const filename = match ? match[1] : "output";
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

const handleSubmit = async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const endpoint = form.getAttribute("data-endpoint");
  const fileInputs = Array.from(form.querySelectorAll('input[type="file"]'));
  const textInputs = Array.from(form.querySelectorAll('input[type="text"], input[type="number"]'));
  const selectionInputs = Array.from(form.querySelectorAll("[data-require-selection]"));

  const hasFiles = fileInputs.length === 0 || fileInputs.some((input) => input.files && input.files.length > 0);
  const missingRequiredText = textInputs.some((input) => input.required && !(input.value || "").trim());

  if (!hasFiles) {
    setStatus(form, "Please select a file before submitting.", true);
    return;
  }

  if (missingRequiredText) {
    setStatus(form, "Please fill in all required fields.", true);
    return;
  }

  const missingSelection = selectionInputs.some((input) => !(input.value || "").trim());
  if (missingSelection) {
    setStatus(form, "Please select pages before submitting.", true);
    return;
  }

  const formData = new FormData(form);

  try {
    setStatus(form, "Processing...");
    const response = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Request failed");
    }

    const contentType = response.headers.get("Content-Type") || "";
    if (contentType.includes("application/json")) {
      const data = await response.json();
      setStatus(form, "Success! Text copied below.");
      alert(data.text);
      return;
    }

    await downloadBlob(response);
    setStatus(form, "Success! Download started.");
  } catch (err) {
    setStatus(form, err.message, true);
  }
};

tools.forEach((tool) => tool.addEventListener("submit", handleSubmit));

const dropzones = document.querySelectorAll(".dropzone");

dropzones.forEach((zone) => {
  const input = zone.querySelector("input[type=file]");
  const label = zone.querySelector("span");

  if (label && !label.dataset.default) {
    label.dataset.default = label.textContent;
  }

  const updateLabel = () => {
    const files = Array.from(input.files || []);
    if (!label) return;
    if (files.length === 0) {
      label.textContent = label.dataset.default || "Drop file or click to upload";
      return;
    }
    label.textContent = files.map((f) => f.name).join(", ");
  };

  input.addEventListener("change", updateLabel);
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.style.borderColor = "#3f5efb";
  });

  zone.addEventListener("dragleave", () => {
    zone.style.borderColor = "";
  });

  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.style.borderColor = "";
    input.files = e.dataTransfer.files;
    updateLabel();
  });
});

const themeToggle = document.getElementById("themeToggle");
const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

const applyTheme = (isDark) => {
  document.body.classList.toggle("dark", isDark);
  localStorage.setItem("docuflex-theme", isDark ? "dark" : "light");
  if (themeToggle) {
    themeToggle.setAttribute("aria-pressed", isDark ? "true" : "false");
  }
};

const storedTheme = localStorage.getItem("docuflex-theme");
if (storedTheme) {
  applyTheme(storedTheme === "dark");
} else {
  applyTheme(prefersDark.matches);
}

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const isDark = !document.body.classList.contains("dark");
    applyTheme(isDark);
  });
}

const rangeWrappers = document.querySelectorAll(".range");
rangeWrappers.forEach((wrapper) => {
  const range = wrapper.querySelector("input[type=range]");
  const valueEl = wrapper.querySelector("[data-range-value]") || wrapper.querySelector("#qualityValue");
  if (range && valueEl) {
    const updateValue = () => {
      valueEl.textContent = range.value;
    };
    updateValue();
    range.addEventListener("input", updateValue);
    range.addEventListener("change", updateValue);
  }
});

const initPdfThumbnailUI = () => {
  const reorderInput = document.getElementById("reorderPdfInput");
  const reorderGrid = document.getElementById("reorderGrid");
  const reorderOrderInput = document.getElementById("orderInput");

  const splitInput = document.getElementById("splitPdfInput");
  const splitGrid = document.getElementById("splitGrid");
  const splitPagesInput = document.getElementById("pagesInput");
  const splitCount = document.getElementById("splitCount");

  const renderPdfPages = async (file, container, onItemReady) => {
    container.innerHTML = "";
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/api/pdf/preview", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Preview failed");
    }

    const data = await response.json();
    data.pages.forEach((page) => {
      const item = document.createElement("div");
      item.className = "page-item";
      item.dataset.page = String(page.page);

      const img = document.createElement("img");
      img.src = page.dataUrl;
      img.alt = `Page ${page.page}`;

      const label = document.createElement("span");
      label.textContent = `Page ${page.page}`;

      item.appendChild(img);
      item.appendChild(label);
      container.appendChild(item);

      if (onItemReady) {
        onItemReady(item);
      }
    });
  };

  if (reorderInput && reorderGrid && reorderOrderInput) {
    const updateOrder = () => {
      const pages = Array.from(reorderGrid.querySelectorAll(".page-item")).map(
        (el) => el.dataset.page
      );
      reorderOrderInput.value = pages.join(",");
    };

    const addDragHandlers = (item) => {
      item.draggable = true;
      item.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("text/plain", item.dataset.page);
        item.classList.add("dragging");
      });
      item.addEventListener("dragend", () => item.classList.remove("dragging"));
      item.addEventListener("dragover", (e) => e.preventDefault());
      item.addEventListener("drop", (e) => {
        e.preventDefault();
        const draggedPage = e.dataTransfer.getData("text/plain");
        const draggedEl = reorderGrid.querySelector(`[data-page="${draggedPage}"]`);
        if (draggedEl && draggedEl !== item) {
          reorderGrid.insertBefore(draggedEl, item);
          updateOrder();
        }
      });
    };

    reorderInput.addEventListener("change", async () => {
      const file = reorderInput.files[0];
      if (!file) return;
      try {
        setStatus(reorderInput.closest("form"), "Loading preview...");
        await renderPdfPages(file, reorderGrid, addDragHandlers);
        updateOrder();
        setStatus(reorderInput.closest("form"), "Preview ready.");
      } catch (err) {
        setStatus(reorderInput.closest("form"), err.message, true);
      }
    });
  }

  if (splitInput && splitGrid && splitPagesInput) {
    const updateSelection = () => {
      const selected = Array.from(splitGrid.querySelectorAll(".page-item.selected")).map(
        (el) => el.dataset.page
      );
      splitPagesInput.value = selected.join(",");
      if (splitCount) {
        splitCount.textContent = `${selected.length} page(s) selected`;
      }
    };

    const addSelectHandlers = (item) => {
      item.addEventListener("click", () => {
        item.classList.toggle("selected");
        updateSelection();
      });
    };

    splitInput.addEventListener("change", async () => {
      const file = splitInput.files[0];
      if (!file) return;
      try {
        setStatus(splitInput.closest("form"), "Loading preview...");
        await renderPdfPages(file, splitGrid, addSelectHandlers);
        updateSelection();
        setStatus(splitInput.closest("form"), "Preview ready.");
      } catch (err) {
        setStatus(splitInput.closest("form"), err.message, true);
      }
    });
  }
};

initPdfThumbnailUI();
