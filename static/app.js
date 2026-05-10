const state = {
  editingCatalogRecordId: null,
  catalogItems: [],
  catalogMetadataItems: [],
  catalogRequestSerial: 0,
};

const CATALOG_RESULT_LIMIT = 300;

let elements;

async function init() {
  elements = {
    statTotal: document.getElementById('statTotal'),
    statOwned: document.getElementById('statOwned'),
    statMissing: document.getElementById('statMissing'),
    statQuantity: document.getElementById('statQuantity'),
    openCatalogEditorButton: document.getElementById('openCatalogEditorButton'),
    closeCatalogEditorButton: document.getElementById('closeCatalogEditorButton'),
    newCatalogItemButton: document.getElementById('newCatalogItemButton'),
    catalogEditorPanel: document.getElementById('catalogEditorPanel'),
    catalogEditorTitle: document.getElementById('catalogEditorTitle'),
    catalogItemForm: document.getElementById('catalogItemForm'),
    catalogItemId: document.getElementById('catalogItemId'),
    catalogEditFranchise: document.getElementById('catalogEditFranchise'),
    catalogEditProperty: document.getElementById('catalogEditProperty'),
    catalogEditProductLine: document.getElementById('catalogEditProductLine'),
    catalogEditManufacturer: document.getElementById('catalogEditManufacturer'),
    catalogEditItemName: document.getElementById('catalogEditItemName'),
    catalogEditWave: document.getElementById('catalogEditWave'),
    catalogEditReleaseYear: document.getElementById('catalogEditReleaseYear'),
    catalogEditReleaseType: document.getElementById('catalogEditReleaseType'),
    catalogEditSourceName: document.getElementById('catalogEditSourceName'),
    catalogEditSourceUrl: document.getElementById('catalogEditSourceUrl'),
    catalogEditImageUrl: document.getElementById('catalogEditImageUrl'),
    catalogEditPackagedImageUrl: document.getElementById('catalogEditPackagedImageUrl'),
    catalogEditNotes: document.getElementById('catalogEditNotes'),
    catalogEditorSubmitButton: document.getElementById('catalogEditorSubmitButton'),
    catalogEditorMessage: document.getElementById('catalogEditorMessage'),
    catalogSearchInput: document.getElementById('catalogSearchInput'),
    catalogFranchiseFilter: document.getElementById('catalogFranchiseFilter'),
    catalogPropertyFilter: document.getElementById('catalogPropertyFilter'),
    catalogProductLineFilter: document.getElementById('catalogProductLineFilter'),
    catalogManufacturerFilter: document.getElementById('catalogManufacturerFilter'),
    catalogReleaseTypeFilter: document.getElementById('catalogReleaseTypeFilter'),
    catalogOwnedFilter: document.getElementById('catalogOwnedFilter'),
    catalogConditionFilter: document.getElementById('catalogConditionFilter'),
    catalogYearFrom: document.getElementById('catalogYearFrom'),
    catalogYearTo: document.getElementById('catalogYearTo'),
    catalogVariantToggle: document.getElementById('catalogVariantToggle'),
    refreshPricingButton: document.getElementById('refreshPricingButton'),
    catalogList: document.getElementById('catalogList'),
    catalogBreakdown: document.getElementById('catalogBreakdown'),
    catalogMessage: document.getElementById('catalogMessage'),
    catalogCardTemplate: document.getElementById('catalogCardTemplate'),
    catalogStatTotal: document.getElementById('catalogStatTotal'),
    catalogStatFranchises: document.getElementById('catalogStatFranchises'),
    catalogStatVintage: document.getElementById('catalogStatVintage'),
    catalogStatModern: document.getElementById('catalogStatModern'),
  };
  bindEvents();
  resetCatalogEditor();
  await bootstrapCatalogFilters();
  await fetchCatalogSummary();
  await fetchCatalogItems();
}

function setCatalogMessage(message, isError = false) {
  elements.catalogMessage.textContent = message;
  elements.catalogMessage.style.color = isError ? '#9d2f2f' : '';
}

function setEditorMessage(message, isError = false) {
  elements.catalogEditorMessage.textContent = message;
  elements.catalogEditorMessage.style.color = isError ? '#9d2f2f' : '';
}

function splitVariantNotes(notes) {
  const text = (notes || '').trim();
  const marker = 'Variant detail:';
  const index = text.indexOf(marker);
  if (index === -1) {
    return { summary: text, variant: '' };
  }
  return {
    summary: text.slice(0, index).trim(),
    variant: text.slice(index + marker.length).trim(),
  };
}

function getInventoryStatusClass(status) {
  if (status === 'complete') return 'complete';
  if (status === 'partial') return 'partial';
  return 'missing';
}

function getCatalogGroupKey(item) {
  return [
    item.franchise,
    item.property_name,
    item.product_line,
    item.manufacturer,
    item.release_year,
    item.wave,
    item.item_name,
    item.release_type,
  ].join('||');
}

function scoreCatalogRepresentative(item) {
  const variant = splitVariantNotes(item.notes).variant.toLowerCase();
  let score = 0;
  if (variant.includes('common version')) score += 7;
  if (variant.includes('regular ') || variant.includes('regular version')) score += 6;
  if (variant.includes('standard ') || variant.includes('standard counterpart')) score += 5;
  if (variant.includes('neutral-expression')) score += 2;
  if (variant.includes('soft-goods')) score += 2;
  if (variant.includes('blond-hair') || variant.includes('blonde-hair')) score += 1;
  if (variant.includes('early ')) score -= 4;
  if (variant.includes('vinyl-cape')) score -= 5;
  if (variant.includes('lighter-blue')) score -= 4;
  if (variant.includes('no country-of-origin') || variant.includes('no-coo')) score -= 4;
  if (variant.includes('blue-lightsaber')) score -= 3;
  if (variant.includes('hollow-cheeks')) score -= 2;
  if (variant.includes('brown snake')) score -= 2;
  if (variant.includes('smiling-mouth')) score -= 1;
  return score;
}

function chooseRepresentativeCatalogItem(group) {
  return [...group].sort((left, right) => scoreCatalogRepresentative(right) - scoreCatalogRepresentative(left))[0];
}

function collapseCatalogVariants(items) {
  const groups = new Map();
  for (const item of items) {
    const key = getCatalogGroupKey(item);
    const current = groups.get(key);
    if (current) {
      current.push(item);
    } else {
      groups.set(key, [item]);
    }
  }

  return [...groups.values()].map((group) => {
    if (group.length === 1) return group[0];
    const representative = chooseRepresentativeCatalogItem(group);
    const variants = [...new Set(group.map((item) => splitVariantNotes(item.notes).variant).filter(Boolean))];
    const summary = splitVariantNotes(representative.notes).summary;
    return {
      ...representative,
      notes: summary || group[0].notes,
      variant_summary: `${group.length} variants available${variants.length ? `: ${variants.join(' | ')}` : '. Expand variants to view each version.'}`,
      variant_count: group.length,
    };
  });
}

function getCatalogDisplayItems(items) {
  return elements.catalogVariantToggle.checked ? items : collapseCatalogVariants(items);
}

function showCatalogImageSlot(mediaGrid, media, image, status, primaryUrl, fallbackUrl, altText) {
  const urls = [primaryUrl, fallbackUrl].filter(Boolean);
  if (!urls.length) return;

  let urlIndex = 0;
  let timeoutId = null;
  const scheduleTimeout = () => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => {
      if (image.classList.contains('loading')) {
        status.textContent = 'Still waiting for this photo source...';
      }
    }, 8000);
  };
  image.alt = altText;
  image.loading = 'eager';
  image.decoding = 'async';
  status.textContent = 'Waiting to download...';
  image.classList.add('loading');
  media.classList.remove('hidden');
  mediaGrid.classList.remove('hidden');

  image.addEventListener('load', () => {
    window.clearTimeout(timeoutId);
    image.classList.remove('loading');
    image.classList.remove('failed');
    status.textContent = 'Photo loaded.';
  });
  image.addEventListener('error', () => {
    urlIndex += 1;
    if (urlIndex < urls.length) {
      image.classList.add('loading');
      image.classList.remove('failed');
      status.textContent = 'Proxy failed; trying original source...';
      image.src = urls[urlIndex];
      scheduleTimeout();
      return;
    }

    window.clearTimeout(timeoutId);
    image.removeAttribute('src');
    image.classList.remove('loading');
    image.classList.add('failed');
    status.textContent = 'Photo not available from proxy or original source.';
  });
  image.src = urls[urlIndex];
  scheduleTimeout();
}

function updateStatsFromSummary(summary) {
  elements.statTotal.textContent = String(summary.total_items ?? 0);
  elements.statOwned.textContent = String(summary.total_inventoried_items ?? 0);
  elements.statMissing.textContent = summary.total_net_value_display ?? '$0.00';
  elements.statQuantity.textContent = String((summary.property_breakdown ?? []).length);
}

function updateCatalogStats(summary) {
  updateStatsFromSummary(summary);
  elements.catalogStatTotal.textContent = String(summary.total_items ?? 0);
  elements.catalogStatFranchises.textContent = String(summary.franchises ?? 0);
  elements.catalogStatVintage.textContent = String(summary.vintage_items ?? 0);
  elements.catalogStatModern.textContent = String(summary.modern_or_reissue_items ?? 0);

  elements.catalogBreakdown.innerHTML = '';
  const fragment = document.createDocumentFragment();
  for (const row of summary.property_breakdown ?? []) {
    const pill = document.createElement('span');
    pill.className = 'breakdown-pill';
    pill.textContent = `${row.property}: ${row.owned_count} (${row.total_value_display})`;
    pill.style.cursor = 'pointer';
    pill.title = `Click to filter catalog to ${row.property} only`;
    pill.addEventListener('click', () => {
      elements.catalogPropertyFilter.value = row.property;
      fetchCatalogItems().catch((error) => {
        setCatalogMessage(`Unable to filter catalog: ${error.message}`, true);
      });
    });
    fragment.appendChild(pill);
  }
  elements.catalogBreakdown.appendChild(fragment);
}

function populateCatalogSelect(select, values, allLabel, preferredValue = null) {
  const currentValue = preferredValue ?? select.value;
  select.innerHTML = '';
  const defaultOption = document.createElement('option');
  defaultOption.value = 'all';
  defaultOption.textContent = allLabel;
  select.appendChild(defaultOption);

  for (const value of values) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }

  select.value = values.includes(currentValue) ? currentValue : 'all';
}

function getCatalogMetadata(items, key) {
  return [...new Set(items.map((item) => item[key]).filter(Boolean))].sort((left, right) => left.localeCompare(right));
}

function updateDependentCatalogFilters(items) {
  const franchiseValue = elements.catalogFranchiseFilter.value;
  const scopedByFranchise = franchiseValue !== 'all'
    ? items.filter((item) => item.franchise === franchiseValue)
    : items;
  const propertyOptions = getCatalogMetadata(scopedByFranchise, 'property_name');
  const propertyValue = propertyOptions.includes(elements.catalogPropertyFilter.value)
    ? elements.catalogPropertyFilter.value
    : 'all';
  const scopedByProperty = propertyValue !== 'all'
    ? scopedByFranchise.filter((item) => item.property_name === propertyValue)
    : scopedByFranchise;
  const productLineOptions = getCatalogMetadata(scopedByProperty, 'product_line');
  const productLineValue = productLineOptions.includes(elements.catalogProductLineFilter.value)
    ? elements.catalogProductLineFilter.value
    : 'all';

  populateCatalogSelect(elements.catalogPropertyFilter, propertyOptions, 'All properties', propertyValue);
  populateCatalogSelect(elements.catalogProductLineFilter, productLineOptions, 'All product lines', productLineValue);
}

function readWholeNumberInput(input) {
  return Math.max(0, Number.parseInt(input.value || '0', 10) || 0);
}

function getInventoryPayloadForCounts(item, inputs) {
  const inventory = item.inventory_record || {};
  const quantity = readWholeNumberInput(inputs.owned);
  const completeCount = Math.min(readWholeNumberInput(inputs.complete), quantity);
  const packagedCount = Math.min(readWholeNumberInput(inputs.packaged), quantity);
  const sealedCount = Math.min(readWholeNumberInput(inputs.sealed), quantity);

  return {
    owned: quantity > 0,
    quantity_owned: quantity,
    condition: inventory.condition || '',
    complete_count: completeCount,
    packaged_count: packagedCount,
    sealed_count: sealedCount,
    storage_location: inventory.storage_location || '',
    ownership_notes: inputs.notes.value.trim(),
  };
}

async function saveQuickCounts(item, inputs, button) {
  const previousText = button.textContent;
  button.disabled = true;
  button.textContent = 'Saving';

  const response = await fetch(`/api/catalog-items/${item.id}/inventory`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(getInventoryPayloadForCounts(item, inputs)),
  });
  const data = await response.json();
  if (!response.ok) {
    button.disabled = false;
    button.textContent = previousText;
    throw new Error(data.error || 'Unable to save counts and notes.');
  }

  await fetchCatalogSummary();
  await fetchCatalogItems();
  setCatalogMessage(`Updated ${data.item_name} counts.`);
}

function renderCatalogItems(items) {
  elements.catalogList.innerHTML = '';
  const displayItems = getCatalogDisplayItems(items);
  if (!displayItems.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = 'No catalog entries match these filters yet.';
    elements.catalogList.appendChild(empty);
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const item of displayItems) {
    const node = elements.catalogCardTemplate.content.cloneNode(true);
    const mediaGrid = node.querySelector('.catalog-media-grid');
    const looseMedia = node.querySelector('.catalog-loose-media');
    const packagedMedia = node.querySelector('.catalog-packaged-media');
    const looseImage = node.querySelector('.catalog-loose-image');
    const packagedImage = node.querySelector('.catalog-packaged-image');
    const looseStatus = node.querySelector('.catalog-loose-status');
    const packagedStatus = node.querySelector('.catalog-packaged-status');
    const statusDot = node.querySelector('.catalog-status-dot');
    node.querySelector('.catalog-franchise').textContent = item.franchise;
    node.querySelector('.catalog-item-name').textContent = item.item_name;

    const releaseType = node.querySelector('.catalog-release-type');
    releaseType.textContent = item.release_type;
    releaseType.classList.add(item.release_type === 'vintage' ? 'owned' : 'missing');

    showCatalogImageSlot(
      mediaGrid,
      looseMedia,
      looseImage,
      looseStatus,
      item.image_url,
      item.raw_image_url,
      `${item.item_name} loose figure photo`,
    );
    showCatalogImageSlot(
      mediaGrid,
      packagedMedia,
      packagedImage,
      packagedStatus,
      item.packaged_image_url,
      item.raw_packaged_image_url,
      `${item.item_name} packaged figure photo`,
    );

    const inventorySummary = item.inventory_summary || {
      quantity_owned: 0,
      complete_count: 0,
      sealed_count: 0,
      original_packaging_count: 0,
      status: 'missing',
      condition: '',
      storage_location: '',
      ownership_notes: '',
    };
    statusDot.classList.add(getInventoryStatusClass(inventorySummary.status));
    node.querySelector('.catalog-owned-quantity').textContent = String(inventorySummary.quantity_owned ?? 0);
    node.querySelector('.catalog-complete-count').textContent = String(inventorySummary.complete_count ?? 0);
    node.querySelector('.catalog-packaging-count').textContent = String(inventorySummary.original_packaging_count ?? 0);
    node.querySelector('.catalog-sealed-count').textContent = String(inventorySummary.sealed_count ?? 0);

    const quickForm = node.querySelector('.quick-counts-form');
    const quickInputs = {
      owned: node.querySelector('.quick-owned-input'),
      complete: node.querySelector('.quick-complete-input'),
      packaged: node.querySelector('.quick-packaging-input'),
      sealed: node.querySelector('.quick-sealed-input'),
      notes: node.querySelector('.quick-owned-notes-input'),
    };
    const quickButton = node.querySelector('.quick-counts-button');
    quickInputs.owned.value = String(inventorySummary.quantity_owned ?? 0);
    quickInputs.complete.value = String(inventorySummary.complete_count ?? 0);
    quickInputs.packaged.value = String(inventorySummary.original_packaging_count ?? 0);
    quickInputs.sealed.value = String(inventorySummary.sealed_count ?? 0);
    quickInputs.notes.value = inventorySummary.ownership_notes || '';
    quickForm.addEventListener('submit', (event) => {
      event.preventDefault();
      saveQuickCounts(item, quickInputs, quickButton).catch((error) => setCatalogMessage(error.message, true));
    });

    const pricingSummary = item.pricing_summary || {};
    node.querySelector('.catalog-price-range').textContent = pricingSummary.display_range || 'Unavailable';
    node.querySelector('.catalog-price-source').textContent = pricingSummary.label || pricingSummary.source || 'Not priced yet';
    node.querySelector('.catalog-price-updated').textContent = pricingSummary.updated_at || 'Not refreshed yet';
    const priceLink = node.querySelector('.catalog-price-link');
    if (pricingSummary.source_url) {
      priceLink.href = pricingSummary.source_url;
      priceLink.textContent = pricingSummary.source || 'Open source';
    } else {
      priceLink.removeAttribute('href');
      priceLink.textContent = 'Unavailable';
    }

    node.querySelector('.catalog-property').textContent = item.property_name;
    node.querySelector('.catalog-product-line').textContent = item.product_line;
    node.querySelector('.catalog-manufacturer').textContent = item.manufacturer;
    node.querySelector('.catalog-release-year').textContent = String(item.release_year);
    node.querySelector('.catalog-wave').textContent = item.wave || 'Unspecified';

    const sourceLink = node.querySelector('.catalog-source-link');
    if (item.source_url) {
      sourceLink.href = item.source_url;
      sourceLink.textContent = item.source_name || 'View source';
    } else {
      sourceLink.removeAttribute('href');
      sourceLink.textContent = item.source_name || 'Unavailable';
    }

    const { summary, variant } = splitVariantNotes(item.notes);
    const variantBlock = node.querySelector('.catalog-variant');
    const variantText = node.querySelector('.catalog-variant-text');
    const ownedNotesBlock = node.querySelector('.owned-notes-display');
    const ownedNotesText = node.querySelector('.owned-notes-text');
    const notes = node.querySelector('.catalog-notes');
    const finalVariant = item.variant_summary || variant;
    if (finalVariant) {
      variantText.textContent = finalVariant;
      variantBlock.classList.remove('hidden');
    }

    if (inventorySummary.ownership_notes) {
      ownedNotesText.textContent = inventorySummary.ownership_notes;
      ownedNotesBlock.classList.remove('hidden');
    }

    const inventoryNoteBits = [
      inventorySummary.condition ? `Condition: ${inventorySummary.condition}` : '',
      inventorySummary.storage_location ? `Location: ${inventorySummary.storage_location}` : '',
    ].filter(Boolean);
    const renderedNotes = [summary || '', ...inventoryNoteBits].filter(Boolean).join('\n\n');
    notes.textContent = renderedNotes || 'No catalog notes.';

    node.querySelector('.catalog-record-edit-button').addEventListener('click', () => openCatalogEditor(item));
    fragment.appendChild(node);
  }

  elements.catalogList.appendChild(fragment);
}

async function fetchCatalogSummary() {
  const response = await fetch('/api/catalog-summary');
  if (!response.ok) throw new Error('Unable to load catalog summary.');
  const summary = await response.json();
  updateCatalogStats(summary);
}

async function fetchCatalogItems() {
  const requestSerial = ++state.catalogRequestSerial;
  const params = new URLSearchParams({
    search: elements.catalogSearchInput.value.trim(),
    franchise: elements.catalogFranchiseFilter.value,
    property_name: elements.catalogPropertyFilter.value,
    product_line: elements.catalogProductLineFilter.value,
    manufacturer: elements.catalogManufacturerFilter.value,
    release_type: elements.catalogReleaseTypeFilter.value,
    owned: elements.catalogOwnedFilter.value,
    condition: elements.catalogConditionFilter.value,
    limit: String(CATALOG_RESULT_LIMIT),
  });

  const yearFrom = elements.catalogYearFrom.value.trim();
  const yearTo = elements.catalogYearTo.value.trim();
  if (yearFrom) params.set('year_from', yearFrom);
  if (yearTo) params.set('year_to', yearTo);

  const response = await fetch(`/api/catalog-items?${params.toString()}`);
  const data = await response.json();
  if (requestSerial !== state.catalogRequestSerial) return;
  if (!response.ok) throw new Error(data.error || 'Unable to load catalog items.');

  state.catalogItems = data;
  renderCatalogItems(data);
  const displayCount = getCatalogDisplayItems(data).length;
  const suffix = elements.catalogVariantToggle.checked ? '' : ` from ${data.length} source entries`;
  const isTruncated = response.headers.get('X-Catalog-Result-Truncated') === 'true';
  const capMessage = isTruncated ? ` Showing first ${CATALOG_RESULT_LIMIT}; narrow search or filters for more.` : '';
  setCatalogMessage(`${displayCount} catalog cards shown${suffix}.${capMessage}`);
}

async function refreshCatalogPricing() {
  elements.refreshPricingButton.disabled = true;
  setCatalogMessage('Refreshing catalog prices...');
  const response = await fetch('/api/catalog-pricing-refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ limit: 25 }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Unable to refresh catalog prices.');
  await fetchCatalogItems();
  setCatalogMessage(`Pricing refresh attempted for ${data.attempted} items; updated ${data.updated}.`);
  elements.refreshPricingButton.disabled = false;
}

async function bootstrapCatalogFilters() {
  const response = await fetch('/api/catalog-filter-options');
  if (!response.ok) throw new Error('Unable to load catalog metadata.');
  const items = await response.json();
  state.catalogMetadataItems = items;
  populateCatalogSelect(elements.catalogFranchiseFilter, getCatalogMetadata(items, 'franchise'), 'All franchises');
  populateCatalogSelect(elements.catalogPropertyFilter, getCatalogMetadata(items, 'property_name'), 'All properties');
  populateCatalogSelect(elements.catalogProductLineFilter, getCatalogMetadata(items, 'product_line'), 'All product lines');
  populateCatalogSelect(elements.catalogManufacturerFilter, getCatalogMetadata(items, 'manufacturer'), 'All manufacturers');
  updateDependentCatalogFilters(state.catalogMetadataItems);
}

function resetCatalogEditor() {
  state.editingCatalogRecordId = null;
  elements.catalogItemForm.reset();
  elements.catalogItemId.value = '';
  elements.catalogEditSourceName.value = 'Manual';
  elements.catalogEditReleaseType.value = 'vintage';
  elements.catalogEditorTitle.textContent = 'Add catalog item';
  elements.catalogEditorSubmitButton.textContent = 'Save catalog item';
  setEditorMessage('');
}

function openCatalogEditor(item = null) {
  elements.catalogEditorPanel.classList.remove('hidden');
  resetCatalogEditor();
  if (item) {
    state.editingCatalogRecordId = item.id;
    elements.catalogItemId.value = String(item.id);
    elements.catalogEditFranchise.value = item.franchise || '';
    elements.catalogEditProperty.value = item.property_name || '';
    elements.catalogEditProductLine.value = item.product_line || '';
    elements.catalogEditManufacturer.value = item.manufacturer || '';
    elements.catalogEditItemName.value = item.item_name || '';
    elements.catalogEditWave.value = item.wave || '';
    elements.catalogEditReleaseYear.value = String(item.release_year || '');
    elements.catalogEditReleaseType.value = item.release_type || 'vintage';
    elements.catalogEditSourceName.value = item.source_name || 'Manual';
    elements.catalogEditSourceUrl.value = item.source_url || '';
    elements.catalogEditImageUrl.value = item.raw_image_url || item.image_url || '';
    elements.catalogEditPackagedImageUrl.value = item.raw_packaged_image_url || item.packaged_image_url || '';
    elements.catalogEditNotes.value = item.notes || '';
    elements.catalogEditorTitle.textContent = 'Edit catalog item';
    elements.catalogEditorSubmitButton.textContent = 'Update catalog item';
    setEditorMessage(`Editing ${item.item_name}.`);
  }
  elements.catalogEditorPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function readCatalogEditorForm() {
  return {
    franchise: elements.catalogEditFranchise.value.trim(),
    property_name: elements.catalogEditProperty.value.trim(),
    product_line: elements.catalogEditProductLine.value.trim(),
    manufacturer: elements.catalogEditManufacturer.value.trim(),
    item_name: elements.catalogEditItemName.value.trim(),
    wave: elements.catalogEditWave.value.trim(),
    release_year: elements.catalogEditReleaseYear.value,
    release_type: elements.catalogEditReleaseType.value,
    source_name: elements.catalogEditSourceName.value.trim(),
    source_url: elements.catalogEditSourceUrl.value.trim(),
    image_url: elements.catalogEditImageUrl.value.trim(),
    packaged_image_url: elements.catalogEditPackagedImageUrl.value.trim(),
    notes: elements.catalogEditNotes.value.trim(),
  };
}

async function saveCatalogItem(event) {
  event.preventDefault();
  const editingId = state.editingCatalogRecordId;
  const url = editingId === null ? '/api/catalog-items' : `/api/catalog-items/${editingId}`;
  const method = editingId === null ? 'POST' : 'PUT';
  elements.catalogEditorSubmitButton.disabled = true;
  setEditorMessage('Saving catalog item...');

  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(readCatalogEditorForm()),
  });
  const data = await response.json();
  elements.catalogEditorSubmitButton.disabled = false;
  if (!response.ok) {
    setEditorMessage(data.error || 'Unable to save catalog item.', true);
    return;
  }

  await bootstrapCatalogFilters();
  await fetchCatalogSummary();
  await fetchCatalogItems();
  openCatalogEditor(data);
  setEditorMessage('Catalog item saved.');
}

function bindEvents() {
  elements.openCatalogEditorButton.addEventListener('click', () => openCatalogEditor());
  elements.closeCatalogEditorButton.addEventListener('click', () => elements.catalogEditorPanel.classList.add('hidden'));
  elements.newCatalogItemButton.addEventListener('click', resetCatalogEditor);
  elements.catalogItemForm.addEventListener('submit', saveCatalogItem);

  const catalogControls = [
    elements.catalogSearchInput,
    elements.catalogFranchiseFilter,
    elements.catalogPropertyFilter,
    elements.catalogProductLineFilter,
    elements.catalogManufacturerFilter,
    elements.catalogReleaseTypeFilter,
    elements.catalogOwnedFilter,
    elements.catalogConditionFilter,
    elements.catalogYearFrom,
    elements.catalogYearTo,
  ];

  for (const control of catalogControls) {
    control.addEventListener('input', () => {
      updateDependentCatalogFilters(state.catalogMetadataItems);
      fetchCatalogItems().catch((error) => setCatalogMessage(error.message, true));
    });
    control.addEventListener('change', () => {
      updateDependentCatalogFilters(state.catalogMetadataItems);
      fetchCatalogItems().catch((error) => setCatalogMessage(error.message, true));
    });
  }

  elements.catalogVariantToggle.addEventListener('change', () => {
    renderCatalogItems(state.catalogItems);
    const displayCount = getCatalogDisplayItems(state.catalogItems).length;
    const suffix = elements.catalogVariantToggle.checked ? '' : ` from ${state.catalogItems.length} source entries`;
    setCatalogMessage(`${displayCount} catalog cards shown${suffix}.`);
  });

  elements.refreshPricingButton.addEventListener('click', () => {
    refreshCatalogPricing().catch((error) => {
      elements.refreshPricingButton.disabled = false;
      setCatalogMessage(error.message, true);
    });
  });
}

init().catch((error) => {
  if (elements) {
    setEditorMessage('Unable to load catalog editor.', true);
    setCatalogMessage(error.message || 'Unable to load catalog.', true);
  } else {
    console.error('Initialization failed:', error.message);
  }
});
