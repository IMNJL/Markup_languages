const socket = io();

async function loadCurrent() {
    const r = await fetch('/api/current');
    const data = await r.json();
    if (data.error) {
        console.error(data.error);
        return;
    }
    document.getElementById('meta').innerText = `Date: ${data.Date} | PreviousDate: ${data.PreviousDate}`;
    const tbody = document.querySelector('#rates-table tbody');
    tbody.innerHTML = '';
    const select = document.getElementById('currency-select');
    select.innerHTML = '';
    data.Valute.forEach(v => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${v.ID}</td><td>${v.NumCode}</td><td>${v.CharCode}</td><td>${v.Nominal}</td><td>${v.Name}</td><td>${v.Value}</td><td>${v.Previous}</td>`;
        tbody.appendChild(tr);
        const opt = document.createElement('option');
        opt.value = v.CharCode;
        opt.text = `${v.CharCode} — ${v.Name}`;
        select.appendChild(opt);
    });
}

// Chart setup
let chart;

function createChart(labels = [], data = []) {
    const ctx = document.getElementById('chart').getContext('2d');
    if (chart) chart.destroy();
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{label: 'Value', data: data, fill: false, tension: 0.1}]
        },
        options: {
            scales: {x: {display: true}, y: {display: true}}
        }
    });
}

async function loadHistory(code) {
    const r = await fetch(`/api/history/${code}`);
    const arr = await r.json();
    const labels = arr.map(a => new Date(a.timestamp).toLocaleString());
    const data = arr.map(a => a.value);
    createChart(labels, data);
}

// initial load
loadCurrent();

// button
document.getElementById('load-history').addEventListener('click', () => {
    const code = document.getElementById('currency-select').value;
    if (!code) return alert('Выберите валюту');
    loadHistory(code);
});

// socket updates
socket.on('rates_snapshot', payload => {
    console.log('snapshot', payload);
    // простая визуальная индикация: перезагрузим таблицу (в реальном проекте можно обновлять только значения)
    loadCurrent();
    // если на графике выбран код и он присутствует в payload.samples — добавим точку
    const selected = document.getElementById('currency-select').value;
    if (chart && selected) {
        const s = payload.samples.find(x => x.char_code === selected);
        if (s) {
            chart.data.labels.push(new Date(payload.timestamp).toLocaleTimeString());
            chart.data.datasets[0].data.push(s.value);
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            chart.update();
        }
    }
});