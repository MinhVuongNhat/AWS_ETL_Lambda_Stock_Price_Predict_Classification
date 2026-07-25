const BUCKET_URL = "https://my-nasdaq-stock-processed-2026-430970051812-ap-southeast-1-an.s3.ap-southeast-1.amazonaws.com";

let allData = [];

document.addEventListener("DOMContentLoaded", () => {
    fetchLatestData();

    document.getElementById("ticker-search").addEventListener("input", (e) => {
        renderTable(e.target.value);
    });
});

async function fetchLatestData() {
    try {
        // Fetch latest.json to get the latest prediction date and key
        const latestRes = await fetch(`${BUCKET_URL}/predictions/latest.json`);
        
        if (!latestRes.ok) {
            throw new Error(`Failed to fetch latest.json: ${latestRes.status}`);
        }
        
        const latestInfo = await latestRes.json();
        document.getElementById("update-date").textContent = `Data for: ${latestInfo.latest_date}`;

        // Fetch the actual predictions JSON
        const dataRes = await fetch(`${BUCKET_URL}/${latestInfo.prediction_key}`);
        
        if (!dataRes.ok) {
            throw new Error(`Failed to fetch predictions JSON: ${dataRes.status}`);
        }

        allData = await dataRes.json();
        
        // Update summary stats
        updateSummary();
        
        // Render table
        renderTable();
        
    } catch (error) {
        console.error("Error fetching data:", error);
        document.getElementById("table-body").innerHTML = `
            <tr>
                <td colspan="4" class="text-center loading-text" style="color: #ef4444;">
                    Error loading data. Make sure S3 CORS is enabled and bucket is public.<br>
                    ${error.message}
                </td>
            </tr>
        `;
    }
}

function updateSummary() {
    document.getElementById("total-count").textContent = allData.length;
    
    const bullishCount = allData.filter(d => d.Prediction === 1).length;
    const bearishCount = allData.length - bullishCount;
    
    document.getElementById("bullish-count").textContent = bullishCount;
    document.getElementById("bearish-count").textContent = bearishCount;
}

function renderTable(searchQuery = "") {
    const tbody = document.getElementById("table-body");
    tbody.innerHTML = "";

    const query = searchQuery.toUpperCase();
    
    // Filter by search query
    const filteredData = allData.filter(d => d.Symbol.includes(query));

    if (filteredData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center loading-text">No matching tickers found.</td></tr>`;
        return;
    }

    filteredData.forEach((row, index) => {
        const tr = document.createElement("tr");
        
        // Staggered animation delay
        tr.style.animation = `fadeUp 0.3s ease-out ${index * 0.02}s both`;

        const isUp = row.Prediction === 1;
        const badgeClass = isUp ? "up" : "down";
        const badgeText = isUp ? "BULLISH" : "BEARISH";
        
        // Probability is between 0 and 1, convert to percentage
        const prob = (row.Probability * 100).toFixed(1);
        const probColor = isUp ? "var(--bullish)" : "var(--bearish)";
        
        // Signal strength bar width (if it's bearish, probability of going UP is low, 
        // so we can show probability of going DOWN = 100 - prob)
        const displayProb = isUp ? prob : (100 - row.Probability * 100).toFixed(1);

        tr.innerHTML = `
            <td class="ticker-symbol">${row.Symbol}</td>
            <td><span class="badge ${badgeClass}">${badgeText}</span></td>
            <td style="font-weight: 500;">${prob}%</td>
            <td>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-muted);">
                    <span>Confidence</span>
                    <span>${displayProb}%</span>
                </div>
                <div class="prob-bar-container">
                    <div class="prob-bar" style="width: ${displayProb}%; background-color: ${probColor};"></div>
                </div>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
}
