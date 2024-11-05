document.addEventListener('DOMContentLoaded', function () {
    fetch('/obtener_datos_bigquery/')
        .then(response => response.json())
        .then(data => {
            window.categoryOptions = data;
        })
        .catch(error => {
            console.error('Error al obtener datos de BigQuery:', error);
        });

    flatpickr('.fecha-registro', {
        locale: 'es',
        dateFormat: 'Y-m-d'
    });
});

function addItem() {
    const initialMessage = document.getElementById('initial-message');
    if (initialMessage) {
        initialMessage.style.display = 'none';
    }

    const newItem = document.createElement('div');
    newItem.className = 'item';
    const itemNumber = document.getElementById('item-container').children.length + 1;

    newItem.innerHTML = `
        <div class="item-number">Ítem ${itemNumber}</div>
        <div class="input-group">
            <label>Categoría</label>
            <select name="categoria" class="categoria-select" onchange="updateSubcategoryOptions(this)">
                <option value="">Selecciona la categoría</option>
                ${window.categoryOptions ? Object.keys(window.categoryOptions).map(category => `<option value="${category}">${category}</option>`).join('') : ''}
            </select>
        </div>
        <div class="input-group">
            <label>Subcategoría</label>
            <select name="subcategoria" class="subcategoria-select" onchange="updateElementOptions(this)">
                <option value="">Selecciona la subcategoría</option>
            </select>
        </div>
        <div class="input-group">
            <label>Elemento</label>
            <select name="elemento" class="elemento-select" onchange="updateUnit(this)">
                <option value="">Selecciona el elemento</option>
            </select>
        </div>
        <div class="input-group">
            <label>Valor</label>
            <div class="value-input-container">
                <input type="text" placeholder="Ingresa el valor" class="carbon-value" oninput="validateNumberInput(this)">
                <span class="unit-label">-</span>
            </div>
        </div>
        <div class="input-group">
            <label>Fecha de Registro</label>
            <input type="text" class="fecha-registro flatpickr-input" placeholder="Selecciona la fecha">
        </div>
        <button class="remove-image" type="button" onclick="removeItem(this)">
            <i class="fa fa-trash"></i> Eliminar
        </button>
    `;
    document.getElementById('item-container').appendChild(newItem);
    updateItemNumbers();
    flatpickr(newItem.querySelector('.fecha-registro'), {
        locale: 'es',
        dateFormat: 'Y-m-d'
    });
}

function updateSubcategoryOptions(selectElement) {
    const itemContainer = selectElement.parentElement.parentElement;
    const subCategorySelect = itemContainer.querySelector('.subcategoria-select');
    const elementSelect = itemContainer.querySelector('.elemento-select');
    const unitLabel = itemContainer.querySelector('.unit-label');
    subCategorySelect.innerHTML = '<option value="">Selecciona la subcategoría</option>';
    elementSelect.innerHTML = '<option value="">Selecciona el elemento</option>';
    unitLabel.textContent = "-";
    const selectedCategory = selectElement.value;
    const subcategories = window.categoryOptions[selectedCategory] || {};
    for (const subcategory in subcategories) {
        const newOption = document.createElement('option');
        newOption.value = subcategory;
        newOption.textContent = subcategory;
        subCategorySelect.appendChild(newOption);
    }
}

function updateElementOptions(selectElement) {
    const itemContainer = selectElement.parentElement.parentElement;
    const elementSelect = itemContainer.querySelector('.elemento-select');
    const unitLabel = itemContainer.querySelector('.unit-label');
    elementSelect.innerHTML = '<option value="">Selecciona el elemento</option>';
    unitLabel.textContent = "-";
    const selectedSubcategory = selectElement.value;
    const category = itemContainer.querySelector('.categoria-select').value;
    const elements = window.categoryOptions[category][selectedSubcategory] || [];
    elements.forEach(element => {
        const newOption = document.createElement('option');
        newOption.value = element.elemento;
        newOption.textContent = element.elemento;
        newOption.setAttribute("data-unit", element.unidad);
        elementSelect.appendChild(newOption);
    });
}

function updateUnit(selectElement) {
    const itemContainer = selectElement.parentElement.parentElement;
    const unitLabel = itemContainer.querySelector('.unit-label');
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    unitLabel.textContent = selectedOption.getAttribute("data-unit") || "-";
}

function validateNumberInput(input) {
    input.value = input.value.replace(/[^0-9.]/g, '');
}

function removeItem(button) {
    button.parentElement.remove();
    updateItemNumbers();
    if (document.getElementById('item-container').children.length === 0) {
        document.getElementById('initial-message').style.display = 'block';
    }
}

function updateItemNumbers() {
    const items = document.querySelectorAll('.item');
    items.forEach((item, index) => {
        const itemNumber = item.querySelector('.item-number');
        itemNumber.textContent = `Ítem ${index + 1}`;
    });
}

function uploadToBigQuery() {
    const items = document.querySelectorAll('.item');
    const data = [];
    let hasIncompleteItem = false;
    items.forEach(item => {
        const categoria = item.querySelector('.categoria-select').value;
        const subcategoria = item.querySelector('.subcategoria-select').value;
        const elemento = item.querySelector('.elemento-select').value;
        const valor = item.querySelector('.carbon-value').value;
        const unidad = item.querySelector('.unit-label').textContent;
        const fechaRegistro = item.querySelector('.fecha-registro').value;
        if (categoria && subcategoria && elemento && valor && fechaRegistro) {
            data.push({ categoria, subcategoria, elemento, valor, unidad, fechaRegistro });
        } else {
            hasIncompleteItem = true;
        }
    });
    if (hasIncompleteItem) {
        alert('Por favor, completa todos los campos antes de subir.');
        return;
    }
    if (data.length === 0) {
        alert("No hay datos para subir a BigQuery.");
        return;
    }
    fetch('/upload_to_bigquery/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        return response.json().then(data => {
            if (!response.ok) {
                throw data;
            }
            return data;
        });
    })
    .then(result => {
        alert(result.message);
    })
    .catch(errorData => {
        console.error('Error al subir los datos:', errorData);
        alert("Ocurrió un error al subir los datos: " + (errorData.message || 'Error desconocido'));
    });
}

function getCsrfToken() {
    return document.querySelector('input[name="csrfmiddlewaretoken"]').value;
}

// Funciones para manejar los botones y redirigir a las páginas de alcance
function handleConsumo() {
    window.location.href = consumoUrl;
}

function handleTCO2() {
    window.location.href = tco2Url;
}

function handleDistribuidora() {
    window.location.href = distribuidoraUrl;
}

// Inicialización de gráficos con Chart.js
document.addEventListener('DOMContentLoaded', function() {
    var ctx1 = document.getElementById('consumoChart').getContext('2d');
    var consumoChart = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Consumo',
                data: consumoData,
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 3,
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.4,
                pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                pointBorderColor: 'white',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Consumo Mensual',
                    font: { size: 18 }
                },
                legend: {
                    position: 'top',
                    labels: { font: { size: 14 } }
                }
            },
            scales: {
                x: { ticks: { font: { size: 12 } } },
                y: { beginAtZero: true, ticks: { font: { size: 12 } } }
            }
        }
    });

    var ctx2 = document.getElementById('TCO2Chart').getContext('2d');
    var TCO2Chart = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'TCO2',
                data: tco2Data,
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 3,
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.4,
                pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                pointBorderColor: 'white',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'TCO2 Mensual',
                    font: { size: 18 }
                },
                legend: {
                    position: 'top',
                    labels: { font: { size: 14 } }
                }
            },
            scales: {
                x: { ticks: { font: { size: 12 } } },
                y: { beginAtZero: true, ticks: { font: { size: 12 } } }
            }
        }
    });

    var ctx3 = document.getElementById('distribuidoraChart').getContext('2d');
    var distribuidoraChart = new Chart(ctx3, {
        type: 'bar',
        data: {
            labels: distribuidoraLabels,
            datasets: [{
                label: 'Consumo por Distribuidora',
                data: distribuidoraData,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
                hoverBackgroundColor: 'rgba(54, 162, 235, 0.8)',
                hoverBorderColor: 'rgba(54, 162, 235, 1)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Consumo por Distribuidora',
                    font: { size: 18 }
                },
                legend: {
                    position: 'top',
                    labels: { font: { size: 14 } }
                }
            },
            scales: {
                x: { ticks: { font: { size: 12 } } },
                y: { beginAtZero: true, ticks: { font: { size: 12 } } }
            }
        }
    });
});

