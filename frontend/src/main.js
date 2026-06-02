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
  // Destroy old tree if it exists
  if ($('#tree-container').jstree()) {
    $('#tree-container').jstree('destroy');
  }
  treeInstance = null;

  const jsTreeData = convertToJsTreeFormat(data);
  console.log("jsTreeData after conversion:", jsTreeData);

  try {
    // Initialize jstree with direct data
    $('#tree-container').jstree({
      'core': {
        'data': jsTreeData,
        'multiple': false,
        'themes': {
          'icons': false
        }
      },
      'plugins': ['search']
    });

    // Get the instance after initialization and force redraw
    setTimeout(() => {
      treeInstance = $('#tree-container').jstree(true);
      console.log("jstree instance retrieved:", treeInstance);
      console.log("jstree root nodes:", treeInstance.get_node('#').children);
      
      // Force redraw and open all nodes
      treeInstance.redraw(true);
      treeInstance.open_all();
      console.log("Tree nodes forced to open and redraw");
    }, 100);

    // Bind events
    $('#tree-container').off('select_node.jstree').on('select_node.jstree', function (e, data) {
      displayPartDetails(data.node);
    });

    $('#tree-container').off('dblclick.jstree').on('dblclick.jstree', function (e) {
      if (treeInstance) {
        const node = treeInstance.get_node(e.target);
        if (node && node.data && node.data[0] !== undefined) {
          editDescription(node);
        }
      }
    });
  } catch (error) {
    console.error("Error initializing jstree:", error);
  }
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
      console.log("Initializing tree with", treeData.length, "root nodes");
      try {
        initializeTree(treeData);
        console.log("Tree initialization complete");
        partDetails.innerHTML = "Select a part to view details";
        
        // Scroll to tree container
        setTimeout(() => {
          treeContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 200);
      } catch (treeError) {
        console.error("Error in tree initialization:", treeError);
        treeContainer.innerHTML = `Error initializing tree: ${treeError.message}`;
      }
    } else {
      console.error("No tree data or empty treeData:", treeData);
      treeContainer.innerHTML = `No BOM data found in the file. treeData: ${JSON.stringify(treeData)}`;
    }
  } catch (error) {
    console.error("Upload error:", error);
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
window.uploadToBC = uploadToBC;
window.openSettings = openSettings;
window.closeSettings = closeSettings;
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

// Upload to Business Central function
async function uploadToBC() {
  if (!treeData) {
    alert("No BOM data loaded. Please upload and parse a file first.");
    return;
  }

  // Confirm before uploading
  const confirmUpload = confirm(
    "This will upload the BOM data to Business Central. " +
    "Make sure all changes have been made. Continue?"
  );
  
  if (!confirmUpload) {
    return;
  }

  try {
    // Extract flat BOM data from tree structure
    function flattenTree(nodes, parentPartNumber = null) {
      const flattened = [];
      nodes.forEach((node, index) => {
        const nodeData = node.data || [];
        // Create BOM entry
        const bomEntry = {
          "LEVEL": nodeData[9] || 0, // Level from node data
          "PARENT PART NUMBER": parentPartNumber,
          "COMPONENT PART NUMBER": node.text,
          "STATUS": nodeData[1] || "",
          "TYPE": nodeData[2] || "PART",
          "QTY": nodeData[8] || 1,
          "Attrib:SPAREPART": nodeData[6] || "",
          "Attrib:SPAREPART SEVERITY": nodeData[7] || "",
          "Attrib:SPARESLISTQTY": nodeData[8] || ""
        };
        flattened.push(bomEntry);
        
        // Recursively flatten children
        if (node.children && node.children.length > 0) {
          flattened.push(...flattenTree(node.children, node.text));
        }
      });
      return flattened;
    }

    const jsTreeData = convertToJsTreeFormat(treeData);
    const bomDataFlattened = flattenTree(jsTreeData);

    console.log(`Uploading ${bomDataFlattened.length} items to Business Central...`);

    uploadToBCBtn.disabled = true;
    uploadToBCBtn.textContent = "⏳ Uploading to BC...";

    const response = await fetch(`${BACKEND_URL}/api/upload-to-bc`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ bom_data: bomDataFlattened })
    });

    const result = await response.json();

    if (response.ok) {
      alert(
        `✅ Upload Successful!\n\n` +
        `Total items: ${result.total_items}\n` +
        `Batches sent: ${result.batches_sent}\n\n` +
        `Check the backend console for detailed responses.`
      );
    } else {
      alert(`❌ Upload failed: ${result.error || result.message}`);
    }
  } catch (error) {
    alert(`❌ Upload to Business Central failed: ${error.message}`);
    console.error("Upload error:", error);
  } finally {
    uploadToBCBtn.disabled = false;
    uploadToBCBtn.textContent = "📤 Upload to Business Central";
  }
}

// Create upload button and add it to the DOM
const uploadToBCBtn = document.createElement("button");
uploadToBCBtn.textContent = "📤 Upload to Business Central";
uploadToBCBtn.className = "upload-bc-btn";
uploadToBCBtn.style.marginTop = "0";
uploadToBCBtn.style.background = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)";
uploadToBCBtn.style.color = "white";
uploadToBCBtn.style.padding = "0.75rem 1.5rem";
uploadToBCBtn.style.border = "none";
uploadToBCBtn.style.borderRadius = "0.375rem";
uploadToBCBtn.style.cursor = "pointer";
uploadToBCBtn.style.fontSize = "1rem";
uploadToBCBtn.style.fontWeight = "600";
uploadToBCBtn.addEventListener("click", uploadToBC);

// Create settings button
const settingsBtn = document.createElement("button");
settingsBtn.textContent = "⚙️ Settings";
settingsBtn.className = "settings-btn";
settingsBtn.style.marginTop = "0";
settingsBtn.style.background = "linear-gradient(135deg, #718096 0%, #4a5568 100%)";
settingsBtn.style.color = "white";
settingsBtn.style.padding = "0.75rem 1.5rem";
settingsBtn.style.border = "none";
settingsBtn.style.borderRadius = "0.375rem";
settingsBtn.style.cursor = "pointer";
settingsBtn.style.fontSize = "1rem";
settingsBtn.style.fontWeight = "600";
settingsBtn.addEventListener("click", openSettings);

// Add the buttons to the action section
const actionButtonsContainer = document.querySelector("#action-buttons");
actionButtonsContainer.appendChild(uploadToBCBtn);
actionButtonsContainer.appendChild(settingsBtn);

// Update status display with colors
function updateStatusDisplay() {
  // Placeholder for future status display logic
}

// Settings function
function openSettings() {
  const modal = document.getElementById('settings-modal');
  modal.style.display = 'block';
}

function closeSettings() {
  const modal = document.getElementById('settings-modal');
  modal.style.display = 'none';
}

// Close modal when clicking outside of it
window.addEventListener('click', function(event) {
  const modal = document.getElementById('settings-modal');
  if (event.target === modal) {
    modal.style.display = 'none';
  }
});

fetchHealth();
