async function initEPG() {
    try {
        const [xmlRes, m3uRes] = await Promise.all([
            fetch('./epg.xml'),
            fetch('./channels.m3u')
        ]);

        const xmlText = await xmlRes.text();
        const m3uText = await m3uRes.text();
        
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlText, "text/xml");
        const programmes = Array.from(xmlDoc.getElementsByTagName("programme"));
        
        // Match M3U channels to XML data
        const channels = parseM3U(m3uText);
        const container = document.getElementById("epg-grid");
        container.innerHTML = "";

        channels.slice(0, 50).forEach(ch => { // Limit to 50 for performance
            const chProgs = programmes.filter(p => p.getAttribute("channel") === ch.id);
            if (chProgs.length > 0) {
                renderRow(container, ch, chProgs);
            }
        });
    } catch (e) {
        document.getElementById("epg-grid").innerHTML = "Failed to load Guide. Run the GitHub Action first.";
    }
}

function parseM3U(text) {
    return text.split('#EXTINF').slice(1).map(line => ({
        id: line.match(/tvg-id="([^"]+)"/)?.[1],
        logo: line.match(/tvg-logo="([^"]+)"/)?.[1],
        name: line.split(',')[1]?.split('\n')[0].trim()
    })).filter(c => c.id);
}

function renderRow(container, ch, progs) {
    const row = document.createElement("div");
    row.className = "channel-row";
    row.innerHTML = `
        <div class="channel-info">
            <img src="${ch.logo}" onerror="this.src='https://via.placeholder.com/40'">
            <span>${ch.name}</span>
        </div>
        <div class="program-list">
            ${progs.slice(0, 10).map(p => `
                <div class="program-card">
                    <div class="time">${p.getAttribute("start").substring(8,12)}</div>
                    <div class="title">${p.getElementsByTagName("title")[0].textContent}</div>
                </div>
            `).join('')}
        </div>`;
    container.appendChild(row);
}

initEPG();
