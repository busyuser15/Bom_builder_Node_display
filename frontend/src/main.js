const BACKEND_URL = "http://localhost:5000";
const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#bom-file");
const backendStatus = document.querySelector("#backend-status");
const treeContainer = document.querySelector("#tree-container");
const partDetails = document.querySelector("#part-details");
const searchInput = document.querySelector("#search-input");
const searchBtn = document.querySelector("#search-btn");
const resetSearchBtn = document.querySelector("#reset-search-btn");
const expandAllBtn = document.querySelector("#expand-all-btn");
const collapseAllBtn = document.querySelector("#collapse-all-btn");
const searchType = document.querySelector("#search-type");

let treeData = null;
let compValues = {};
let treeInstance = null;
let changes = {
  phantom: [],      // Parts with phantom assembly toggled
  treatAsPart: [],  // Parts with treat as part toggled
  descriptions: {}  // { partNumber: newDescription }
};

async function fetchHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/health`);
    const body = await response.json();
    backendStatus.textContent = body.status === "ok" ? "online" : "offline";
  } catch (error) {
    backendStatus.textContent = "offline";
  }
}

function convertToJsTreeFormat(data) {
  function convertNode(node) {
    return {
      id: node.id,
      text: node.text,
      data: node.values,
      children: node.children ? node.children.map(convertNode) : []
    };
  }
  return data.map(convertNode);
}

function initializeTree(data) {
  if (treeInstance) {
    treeInstance.destroy();
  }

  const jsTreeData = convertToJsTreeFormat(data);

  $('#tree-container').jstree({
    'core': {
      'data': jsTreeData,
      'themes': {
        'icons': false
      }
    },
    'plugins': ['search']
  });

  treeInstance = $('#tree-container').jstree(true);

  // Bind selection event
  $('#tree-container').on('select_node.jstree', function (e, data) {
    displayPartDetails(data.node);
  });

  // Bind double-click for editing
  $('#tree-container').on('dblclick.jstree', function (e) {
    const node = treeInstance.get_node(e.target);
    if (node && node.data && node.data[0] !== undefined) {
      editDescription(node);
    }
  });
}

function displayPartDetails(node) {
  console.log(`displayPartDetails called for node: ${node.id}`);
  console.log(`node.data:`, node.data);
  console.log(`compValues[${node.id}]:`, compValues[node.id]);
  
  const values = node.data;
  if (!values || values.length < 9) {
    partDetails.innerHTML = "No details available";
    return;
  }

  console.log("Values to display:", values);
  
  const details = [
    { label: "Part Number", value: node.text },
    { label: "Description", value: values[0] || "" },
    { label: "Status", value: values[1] || "" },
    { label: "Type", value: values[2] || "" },
    { label: "Phantom Assembly", value: values[3] ? "Yes" : "No", type: "checkbox", key: "phantom" },
    { label: "Treat as Part", value: values[4] ? "Yes" : "No", type: "checkbox", key: "treatAsPart" },
    { label: "Classification", value: values[5] || "" },
    { label: "Spare Parts", value: values[6] || "" },
    { label: "Spare Parts Severity", value: values[7] || "" },
    { label: "Spare Parts Qty", value: values[8] || "" }
  ];

  partDetails.innerHTML = details.map(detail => {
    if (detail.type === "checkbox") {
      const isChecked = values[detail.key === "phantom" ? 3 : 4];
      return `
        <div class="part-detail-row">
          <div class="part-detail-label">${detail.label}:</div>
          <div class="checkbox-control">
            <input type="checkbox" id="${detail.key}-${node.id}" ${isChecked ? "checked" : ""} onchange="updateCheckbox('${node.id}', '${detail.key}', this.checked)">
            <label for="${detail.key}-${node.id}">${isChecked ? "Yes" : "No"}</label>
          </div>
        </div>
      `;
    } else if (detail.label === "Description") {
      return `
        <div class="part-detail-row">
          <div class="part-detail-label">${detail.label}:</div>
          <input type="text" class="edit-description" value="${detail.value}" onchange="updateDescription('${node.id}', this.value)" onblur="saveDescriptionPersist('${node.id}', this.value)">
        </div>
      `;
    } else {
      return `
        <div class="part-detail-row">
          <div class="part-detail-label">${detail.label}:</div>
          <div class="part-detail-value">${detail.value}</div>
        </div>
      `;
    }
  }).join('');
}

function editDescription(node) {
  const currentDesc = node.data[0] || "";
  const newDesc = prompt("Edit description:", currentDesc);
  if (newDesc !== null && newDesc !== currentDesc) {
    updateDescription(node.id, newDesc);
    // Update the tree node text if needed
    treeInstance.rename_node(node, `${node.text} (${newDesc})`);
  }
}

function updateDescription(nodeId, newDesc) {
  console.log(`updateDescription called for ${nodeId} with value: ${newDesc}`);
  
  // Update the tree node data
  const node = treeInstance.get_node(nodeId);
  if (node && node.data) {
    console.log("Before update - node.data[0]:", node.data[0]);
    node.data[0] = newDesc;
    console.log("After update - node.data[0]:", node.data[0]);
    
    // Also update in compValues for backup
    if (!compValues[nodeId]) {
      compValues[nodeId] = [...node.data];
    } else {
      compValues[nodeId][0] = newDesc;
    }
    console.log("Updated compValues[nodeId]:", compValues[nodeId]);
    
    // Track change
    changes.descriptions[nodeId] = newDesc;
    console.log("Current changes.descriptions:", changes.descriptions);
  } else {
    console.error("Could not find node or node.data for", nodeId);
  }
}

function saveDescriptionPersist(nodeId, newDesc) {
  console.log(`saveDescriptionPersist called for ${nodeId} with value: ${newDesc}`);
  updateDescription(nodeId, newDesc);
}

function updateCheckbox(nodeId, key, checked) {
  console.log(`updateCheckbox called for ${nodeId}, key: ${key}, checked: ${checked}`);
  
  const node = treeInstance.get_node(nodeId);
  if (node && node.data) {
    if (key === "phantom") {
      console.log("Before update - node.data[3]:", node.data[3]);
      node.data[3] = checked;
      console.log("After update - node.data[3]:", node.data[3]);
      
      if (!changes.phantom.includes(nodeId)) {
        changes.phantom.push(nodeId);
      }
    } else if (key === "treatAsPart") {
      console.log("Before update - node.data[4]:", node.data[4]);
      node.data[4] = checked;
      console.log("After update - node.data[4]:", node.data[4]);
      
      if (!changes.treatAsPart.includes(nodeId)) {
        changes.treatAsPart.push(nodeId);
      }
    }
    
    // Also update in compValues for backup
    if (!compValues[nodeId]) {
      compValues[nodeId] = [...node.data];
    } else {
      compValues[nodeId] = [...node.data];
    }
    console.log("Updated compValues[nodeId]:", compValues[nodeId]);
    
    // Refresh display to show updated checkbox state
    if (treeInstance.get_selected().includes(nodeId)) {
      console.log("Node is currently selected, refreshing display");
      displayPartDetails(node);
    }
  } else {
    console.error("Could not find node or node.data for", nodeId);
  }
}

function performSearch() {
  const searchTerm = searchInput.value.toLowerCase();
  const searchBy = searchType.value;

  if (!searchTerm) {
    resetSearch();
    return;
  }

  // Close all nodes first
  treeInstance.close_all();

  // Get all nodes
  const allNodes = treeInstance.get_json('#', { flat: true });

  // Find matching nodes
  const matchingNodes = [];
  allNodes.forEach(node => {
    let textToSearch = "";
    if (searchBy === "part") {
      textToSearch = node.text.toLowerCase();
    } else if (searchBy === "description") {
      textToSearch = (node.data && node.data[0] ? node.data[0].toLowerCase() : "");
    }

    if (textToSearch.includes(searchTerm)) {
      matchingNodes.push(node.id);
    }
  });

  // Show matching nodes and their parents
  const nodesToShow = new Set();
  matchingNodes.forEach(nodeId => {
    // Add the node itself
    nodesToShow.add(nodeId);

    // Add all parents
    let parent = treeInstance.get_parent(nodeId);
    while (parent && parent !== '#') {
      nodesToShow.add(parent);
      parent = treeInstance.get_parent(parent);
    }
  });

  // Hide nodes that don't match
  allNodes.forEach(node => {
    if (nodesToShow.has(node.id)) {
      treeInstance.show_node(node.id);
    } else {
      treeInstance.hide_node(node.id);
    }
  });

  // Expand shown nodes
  nodesToShow.forEach(nodeId => {
    treeInstance.open_node(nodeId);
  });
}

function resetSearch() {
  searchInput.value = "";
  treeInstance.show_all();
  treeInstance.close_all();
}

async function uploadFile(event) {
  event.preventDefault();

  if (!fileInput.files.length) {
    alert("Please choose an Excel file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  treeContainer.innerHTML = "Uploading and parsing...";

  try {
    const response = await fetch(`${BACKEND_URL}/api/parse`, {
      method: "POST",
      body: formData,
    });

    const body = await response.json();
    console.log("Response body:", body);
    
    if (!response.ok) {
      treeContainer.innerHTML = `Error: ${body.error || response.statusText}`;
      return;
    }

    treeData = body.tree_data;
    compValues = body.comp_values || {};
    
    console.log("treeData:", treeData);
    console.log("treeData length:", treeData ? treeData.length : "undefined");
    console.log("compValues:", compValues);

    if (treeData && treeData.length > 0) {
      initializeTree(treeData);
      partDetails.innerHTML = "Select a part to view details";
    } else {
      treeContainer.innerHTML = `No BOM data found in the file. treeData: ${JSON.stringify(treeData)}`;
    }
  } catch (error) {
    treeContainer.innerHTML = `Request failed: ${error.message}`;
  }
}

// Event listeners
form.addEventListener("submit", uploadFile);
searchBtn.addEventListener("click", performSearch);
resetSearchBtn.addEventListener("click", resetSearch);
expandAllBtn.addEventListener("click", () => treeInstance && treeInstance.open_all());
collapseAllBtn.addEventListener("click", () => treeInstance && treeInstance.close_all());

// Allow Enter key in search input
searchInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    performSearch();
  }
});

// Make functions globally accessible for inline event handlers
window.updateDescription = updateDescription;
window.saveDescriptionPersist = saveDescriptionPersist;
window.updateCheckbox = updateCheckbox;
window.uploadChanges = uploadChanges;

// Upload changes function
async function uploadChanges() {
  if (Object.keys(changes.descriptions).length === 0 && 
      changes.phantom.length === 0 && 
      changes.treatAsPart.length === 0) {
    alert("No changes to upload");
    return;
  }

  // Build payload similar to tkinter version
  const payload = {
    phantom_changes: changes.phantom,
    treat_as_part_changes: changes.treatAsPart,
    description_changes: changes.descriptions,
    comp_values: compValues
  };

  try {
    const response = await fetch(`${BACKEND_URL}/api/save-changes`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    if (response.ok) {
      alert("Changes uploaded successfully!");
      // Clear changes after successful upload
      changes = {
        phantom: [],
        treatAsPart: [],
        descriptions: {}
      };
    } else {
      alert(`Error uploading changes: ${result.error}`);
    }
  } catch (error) {
    alert(`Upload failed: ${error.message}`);
  }
}

// Create upload button and add it to the DOM
const uploadChangesBtn = document.createElement("button");
uploadChangesBtn.textContent = "💾 Upload Changes";
uploadChangesBtn.className = "upload-changes-btn";
uploadChangesBtn.style.marginTop = "1rem";
uploadChangesBtn.addEventListener("click", uploadChanges);

// Add the button after the file upload form
form.parentElement.appendChild(uploadChangesBtn);

// Update status display with colors
function updateStatusDisplay() {
  const hasChanges = Object.keys(changes.descriptions).length > 0 || 
                     changes.phantom.length > 0 || 
                     changes.treatAsPart.length > 0;
  
  if (hasChanges) {
    uploadChangesBtn.textContent = `💾 Upload Changes (${Object.keys(changes.descriptions).length + changes.phantom.length + changes.treatAsPart.length} changes)`;
    uploadChangesBtn.style.background = "linear-gradient(135deg, #f6ad55 0%, #ed8936 100%)";
  } else {
    uploadChangesBtn.textContent = "💾 Upload Changes";
    uploadChangesBtn.style.background = "linear-gradient(135deg, #48bb78 0%, #38a169 100%)";
  }
}

// Call updateStatusDisplay after each change
const originalUpdateDescription = updateDescription;
window.updateDescription = function(...args) {
  originalUpdateDescription(...args);
  updateStatusDisplay();
};

const originalUpdateCheckbox = updateCheckbox;
window.updateCheckbox = function(...args) {
  originalUpdateCheckbox(...args);
  updateStatusDisplay();
};

fetchHealth();
