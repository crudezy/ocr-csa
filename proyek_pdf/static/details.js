document.addEventListener('DOMContentLoaded', function () {
    // Data JSON dari hasil parse Anda
    const parsedData = [
      { "deskripsi": "HNS SHAMPOO SUPREME ANTI 1.00", "discount": 0, "harga": 52570, "qty": 24, "sku": "4902430869126", "uom": "EACH 06378165" },
      { "deskripsi": "HERBAL ESS SHAMPOO ROSE- 1.00", "discount": 0, "harga": 78912, "qty": 3, "sku": "8001090222909", "uom": "EACH 07576140" },
      { "deskripsi": "HNS SHAMPOO ITCH CARE EUCA- 1.00", "discount": 0, "harga": 48000, "qty": 24, "sku": "4987176046369", "uom": "EACH 07878015" },
      { "deskripsi": "PANTENE CONDITIONER 3MM BI- 1.00", "discount": 0, "harga": 47500, "qty": 12, "sku": "4987176047083", "uom": "EACH 08044143" }
    ];

    const tableBody = document.querySelector('#details-table tbody');
    const addItemBtn = document.getElementById('add-item-btn');

    // Fungsi untuk format mata uang
    const formatCurrency = (amount) => {
        return `Rp ${new Intl.NumberFormat('id-ID').format(amount)}`;
    };

    // Fungsi untuk merender seluruh tabel
    function renderTable() {
        tableBody.innerHTML = '';
        let totalAmount = 0;

        parsedData.forEach((item, index) => {
            const subtotal = item.qty * item.harga;
            totalAmount += subtotal;

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td data-field="deskripsi">${item.deskripsi.replace(/ 1.00|- 1.00/g, '')}</td>
                <td class="col-sku" data-field="sku"><a href="#">${item.sku}</a></td>
                <td data-field="uom">${item.uom.split(' ')[0]}</td>
                <td data-field="qty">${item.qty}</td>
                <td data-field="harga">${formatCurrency(item.harga)}</td>
                <td data-field="discount">${item.discount}%</td>
                <td>${formatCurrency(subtotal)}</td>
                <td><button class="btn-delete">Delete</button></td>
            `;
            tableBody.appendChild(row);
        });
        
        // Update summary cards
        document.getElementById('summary-total-amount').textContent = formatCurrency(totalAmount);
        document.getElementById('item-count').textContent = `${parsedData.length} items in this purchase order`;
    }

    // Fungsi untuk membuat sel menjadi bisa diedit
    tableBody.addEventListener('click', function(e) {
        if (e.target.tagName === 'TD' && e.target.dataset.field) {
            const cell = e.target;
            const originalValue = cell.textContent;
            
            // Hindari edit ulang jika sudah dalam mode edit
            if (cell.querySelector('input')) return;

            const input = document.createElement('input');
            input.type = 'text';
            input.value = originalValue;
            
            cell.innerHTML = '';
            cell.appendChild(input);
            input.focus();

            input.addEventListener('blur', saveChange);
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    saveChange();
                } else if (e.key === 'Escape') {
                    cell.textContent = originalValue;
                }
            });

            function saveChange() {
                cell.textContent = input.value;
                // Di sini Anda bisa menambahkan logika untuk menyimpan perubahan ke array `parsedData`
            }
        }
    });

    // Event listener untuk tombol 'Add Item'
    addItemBtn.addEventListener('click', function() {
        const newRow = document.createElement('tr');
        const itemCount = tableBody.querySelectorAll('tr').length;
        newRow.innerHTML = `
            <td>${itemCount + 1}</td>
            <td data-field="deskripsi">New Product</td>
            <td class="col-sku" data-field="sku"><a href="#">0000000000</a></td>
            <td data-field="uom">EACH</td>
            <td data-field="qty">1</td>
            <td data-field="harga">${formatCurrency(0)}</td>
            <td data-field="discount">0%</td>
            <td>${formatCurrency(0)}</td>
            <td><button class="btn-delete">Delete</button></td>
        `;
        tableBody.appendChild(newRow);
    });

    // Panggil fungsi render untuk pertama kali
    renderTable();
});