const tools = document.querySelectorAll(".tool[data-endpoint]");

const setStatus = (form, text, isError = false) => {
  const status = form.querySelector(".status");
  status.textContent = text;
  status.style.color = isError ? "#d64545" : "";
};

const downloadBlob = async (response, fallbackFilename = "") => {
  const disposition = response.headers.get("Content-Disposition") || "";
  const utf8Match = disposition.match(/filename\*\s*=\s*([^']*)''([^;]+)/i);
  const standardMatch = disposition.match(/filename="?([^\";]+)"?/i);
  const filename = utf8Match
    ? decodeURIComponent(utf8Match[2])
    : standardMatch
      ? standardMatch[1]
      : fallbackFilename || "output";
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

  let formData;
  const isMergeForm = endpoint === "/api/pdf/merge";

  if (isMergeForm) {
    formData = new FormData();
    const mergeInput = form.querySelector("#mergePdfInput");
    const mergeFiles = Array.from((mergeInput && mergeInput._selectedFiles) || (mergeInput && mergeInput.files) || []);
    mergeFiles.forEach((file) => formData.append("files", file));

    const filenameInput = form.querySelector('input[name="filename"]');
    if (filenameInput) {
      formData.append("filename", filenameInput.value);
    }
  } else {
    formData = new FormData(form);
  }

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

    const filenameInput = form.querySelector('input[name="filename"]');
    const fallbackFilename = filenameInput ? filenameInput.value.trim() : "";

    await downloadBlob(response, fallbackFilename);
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

const initMergePdfUI = () => {
  const mergeInput = document.getElementById("mergePdfInput");
  const mergeList = document.getElementById("mergeFileList");

  if (!mergeInput || !mergeList) {
    return;
  }

  let selectedFiles = [];
  let draggedIndex = null;

  const getFileKey = (file) => `${file.name}__${file.size}__${file.lastModified}`;

  const syncInputFiles = () => {
    const dataTransfer = new DataTransfer();
    selectedFiles.forEach((file) => dataTransfer.items.add(file));
    mergeInput.files = dataTransfer.files;
    mergeInput._selectedFiles = selectedFiles.slice();
  };

  const moveFile = (fromIndex, toIndex) => {
    if (fromIndex === toIndex) return;
    if (fromIndex < 0 || toIndex < 0) return;
    if (fromIndex >= selectedFiles.length || toIndex >= selectedFiles.length) return;

    const beforeRects = new Map(
      Array.from(mergeList.querySelectorAll(".file-card")).map((row) => [
        row.dataset.key,
        row.getBoundingClientRect(),
      ])
    );

    const [item] = selectedFiles.splice(fromIndex, 1);
    selectedFiles.splice(toIndex, 0, item);
    syncInputFiles();
    renderList(beforeRects);
  };

  const renderList = (beforeRects = null) => {
    mergeList.innerHTML = "";

    if (selectedFiles.length === 0) {
      mergeList.classList.add("empty");
      mergeList.textContent = "No PDFs selected yet.";
      return;
    }

    mergeList.classList.remove("empty");
    selectedFiles.forEach((file, index) => {
      const fileKey = getFileKey(file);
      const row = document.createElement("div");
      row.className = "file-row file-card";
      row.draggable = true;
      row.dataset.key = fileKey;
      row.dataset.index = String(index);

      const meta = document.createElement("div");
      meta.className = "file-meta";

      const name = document.createElement("strong");
      name.textContent = file.name;

      const order = document.createElement("span");
      order.className = "file-order";
      order.textContent = `File ${index + 1}`;

      const hint = document.createElement("span");
      hint.className = "file-hint";
      hint.textContent = "Drag to reorder";

      const dragHandle = document.createElement("span");
      dragHandle.className = "drag-handle";
      dragHandle.textContent = "⋮⋮";

      const textWrap = document.createElement("div");
      textWrap.className = "file-text";

      meta.appendChild(name);
      meta.appendChild(order);
      meta.appendChild(hint);

      textWrap.appendChild(meta);

      row.appendChild(textWrap);
      row.appendChild(dragHandle);

      row.addEventListener("dragstart", (event) => {
        draggedIndex = index;
        row.classList.add("dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", file.name);
      });

      row.addEventListener("dragend", () => {
        row.classList.remove("dragging");
        draggedIndex = null;
        mergeList.querySelectorAll(".drop-target").forEach((el) => el.classList.remove("drop-target"));
      });

      row.addEventListener("dragover", (event) => {
        event.preventDefault();
        const targetIndex = Number(row.dataset.index);
        if (Number.isNaN(targetIndex) || draggedIndex === null || targetIndex === draggedIndex) return;
        row.classList.add("drop-target");
        event.dataTransfer.dropEffect = "move";
      });

      row.addEventListener("dragleave", () => {
        row.classList.remove("drop-target");
      });

      row.addEventListener("drop", (event) => {
        event.preventDefault();
        row.classList.remove("drop-target");
        const targetIndex = Number(row.dataset.index);
        if (Number.isNaN(targetIndex) || draggedIndex === null) return;

        moveFile(draggedIndex, targetIndex);
        draggedIndex = null;
      });

      mergeList.appendChild(row);
    });

    if (!beforeRects) {
      return;
    }

    requestAnimationFrame(() => {
      mergeList.querySelectorAll(".file-card").forEach((row) => {
        const before = beforeRects.get(row.dataset.key);
        if (!before) return;

        const after = row.getBoundingClientRect();
        const deltaX = before.left - after.left;
        const deltaY = before.top - after.top;
        if (deltaX === 0 && deltaY === 0) return;

        if (typeof row.animate === "function") {
          row.animate(
            [
              { transform: `translate(${deltaX}px, ${deltaY}px)` },
              { transform: "translate(0, 0)" },
            ],
            {
              duration: 260,
              easing: "cubic-bezier(0.2, 0.8, 0.2, 1)",
            }
          );
        } else {
          row.style.transition = "none";
          row.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
          requestAnimationFrame(() => {
            row.style.transition = "transform 260ms cubic-bezier(0.2, 0.8, 0.2, 1)";
            row.style.transform = "";
          });
        }
      });
    });
  };

  mergeInput.addEventListener("change", () => {
    selectedFiles = Array.from(mergeInput.files || []);
    syncInputFiles();
    renderList();
  });

  renderList();
};

const initPdfThumbnailUI = () => {
  const reorderInput = document.getElementById("reorderPdfInput");
  const reorderGrid = document.getElementById("reorderGrid");
  const reorderOrderInput = document.getElementById("orderInput");
  let currentDropTarget = null;

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
    const fragment = document.createDocumentFragment();

    for (let i = 0; i < data.pages.length; i += 1) {
      const page = data.pages[i];
      const item = document.createElement("div");
      item.className = "page-item";
      item.dataset.page = String(page.page);

      const img = document.createElement("img");
      img.src = page.dataUrl;
      img.alt = `Page ${page.page}`;
      img.loading = "lazy";
      img.decoding = "async";

      const label = document.createElement("span");
      label.textContent = `Page ${page.page}`;

      item.appendChild(img);
      item.appendChild(label);
      fragment.appendChild(item);

      if (onItemReady) {
        onItemReady(item);
      }

      if ((i + 1) % 12 === 0) {
        container.appendChild(fragment);
        await new Promise((resolve) => requestAnimationFrame(resolve));
      }
    }

    container.appendChild(fragment);
  };

  if (reorderInput && reorderGrid && reorderOrderInput) {
    const animateReorder = (container, beforeRects) => {
      const items = Array.from(container.querySelectorAll(".page-item"));
      items.forEach((el) => {
        const before = beforeRects.get(el);
        const after = el.getBoundingClientRect();
        if (!before) return;
        const deltaX = before.left - after.left;
        const deltaY = before.top - after.top;
        if (deltaX !== 0 || deltaY !== 0) {
          if (typeof el.animate === "function") {
            el.animate(
              [
                { transform: `translate(${deltaX}px, ${deltaY}px)` },
                { transform: "translate(0, 0)" },
              ],
              {
                duration: 320,
                easing: "cubic-bezier(0.2, 0.8, 0.2, 1)",
              }
            );
          } else {
            el.style.transition = "none";
            el.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
            requestAnimationFrame(() => {
              el.style.transition = "transform 320ms cubic-bezier(0.2, 0.8, 0.2, 1)";
              el.style.transform = "";
              const clearTransition = () => {
                el.style.transition = "";
                el.removeEventListener("transitionend", clearTransition);
              };
              el.addEventListener("transitionend", clearTransition);
            });
          }
        }
      });
    };

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
        e.dataTransfer.effectAllowed = "move";
        item.classList.add("dragging");
      });
      item.addEventListener("dragend", () => {
        item.classList.remove("dragging");
        if (currentDropTarget) {
          currentDropTarget.classList.remove("drop-target");
          currentDropTarget = null;
        }
      });
      item.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        const draggedEl = reorderGrid.querySelector(".page-item.dragging");
        if (!draggedEl || draggedEl === item) return;

        const rect = item.getBoundingClientRect();
        const insertAfter = e.clientX > rect.left + rect.width / 2;
        const referenceNode = insertAfter ? item.nextSibling : item;

        if (referenceNode === draggedEl || draggedEl.nextSibling === referenceNode) {
          return;
        }

        const beforeRects = new Map(
          Array.from(reorderGrid.querySelectorAll(".page-item")).map((el) => [
            el,
            el.getBoundingClientRect(),
          ])
        );

        reorderGrid.insertBefore(draggedEl, referenceNode);
        animateReorder(reorderGrid, beforeRects);
        updateOrder();
      });
      item.addEventListener("dragenter", (e) => {
        e.preventDefault();
        if (item.classList.contains("dragging")) return;
        if (currentDropTarget && currentDropTarget !== item) {
          currentDropTarget.classList.remove("drop-target");
        }
        currentDropTarget = item;
        item.classList.add("drop-target");
      });
      item.addEventListener("dragleave", () => {
        if (currentDropTarget === item) {
          item.classList.remove("drop-target");
          currentDropTarget = null;
        }
      });
      item.addEventListener("drop", (e) => {
        e.preventDefault();
        if (currentDropTarget) {
          currentDropTarget.classList.remove("drop-target");
          currentDropTarget = null;
        }
        const draggedEl = reorderGrid.querySelector(".page-item.dragging");
        if (draggedEl) {
          draggedEl.classList.add("moved");
          setTimeout(() => draggedEl.classList.remove("moved"), 260);
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
initMergePdfUI();
