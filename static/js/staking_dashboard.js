/* ---------------------------------------------------------
   CONFIG
--------------------------------------------------------- */
const API = "https://empireyoncar.duckdns.org/Staking";

/* ---------------------------------------------------------
   ELEMENTOS DEL DOM
--------------------------------------------------------- */
const walletAddressEl = document.getElementById("walletAddress");
const walletBalanceEl = document.getElementById("walletBalance");
const walletRewardsEl = document.getElementById("walletRewards");

const activeTableBody = document.querySelector("#activeStakesTable tbody");
const historyTableBody = document.querySelector("#historyTable tbody");

const toast = document.getElementById("toast");

/* ---------------------------------------------------------
   UTILIDADES
--------------------------------------------------------- */
function shortenAddress(addr) {
    return addr.slice(0, 6) + "..." + addr.slice(-4);
}

function showToast(text, type) {
    toast.innerText = text;
    toast.className = type === "ok" ? "toast-ok" : "toast-err";
    toast.style.display = "block";

    setTimeout(() => {
        toast.style.display = "none";
    }, 3000);
}

function calcProgress(start, end) {
    const now = new Date();
    const s = new Date(start);
    const e = new Date(end);

    const total = e - s;
    const done = now - s;

    let percent = (done / total) * 100;
    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;

    return percent.toFixed(1);
}

/* ---------------------------------------------------------
   CARGAR WALLET
--------------------------------------------------------- */
async function loadWallet() {
    const user_id = localStorage.getItem("user_id");
    if (!user_id) return;

    try {
        const res = await fetch(`${API}/dashboard/balance/${user_id}`);
        const data = await res.json();

        if (data.error) {
            showToast(data.error, "err");
            return;
        }

        walletAddressEl.innerText = shortenAddress(localStorage.getItem("wallet_address"));
        walletBalanceEl.innerText = data.balance.toFixed(2);

    } catch (e) {
        showToast("Error cargando balance", "err");
    }
}

/* ---------------------------------------------------------
   CARGAR RECOMPENSAS
--------------------------------------------------------- */
async function loadRewards() {
    const user_id = localStorage.getItem("user_id");

    try {
        const res = await fetch(`${API}/dashboard/rewards/${user_id}`);
        const data = await res.json();

        walletRewardsEl.innerText = data.rewards.toFixed(4);

    } catch (e) {
        showToast("Error cargando recompensas", "err");
    }
}

/* ---------------------------------------------------------
   CARGAR STAKES ACTIVOS
--------------------------------------------------------- */
async function loadActiveStakes() {
    const user_id = localStorage.getItem("user_id");

    try {
        const res = await fetch(`${API}/dashboard/stakes/${user_id}`);
        const data = await res.json();

        activeTableBody.innerHTML = "";

        data.stakes.forEach(stake => {
            const progress = calcProgress(stake.start_date, stake.end_date);

            const row = `
                <tr>
                    <td>${stake.amount}</td>
                    <td>${stake.apr}%</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress" style="width:${progress}%"></div>
                        </div>
                        <small>${progress}%</small>
                    </td>
                    <td>${stake.reward_acumulada.toFixed(4)}</td>
                    <td>
                        <button onclick="releaseStake('${stake.stake_id}')">Liberar</button>
                        <button class="btn-cancel" onclick="cancelStake('${stake.stake_id}')">Cancelar</button>
                    </td>
                </tr>
            `;

            activeTableBody.innerHTML += row;
        });

    } catch (e) {
        showToast("Error cargando stakes activos", "err");
    }
}

/* ---------------------------------------------------------
   CARGAR HISTORIAL
--------------------------------------------------------- */
async function loadHistory() {
    const user_id = localStorage.getItem("user_id");

    try {
        const res = await fetch(`${API}/dashboard/history/${user_id}`);
        const data = await res.json();

        historyTableBody.innerHTML = "";

        data.history.forEach(stake => {
            const row = `
                <tr>
                    <td>${stake.amount}</td>
                    <td>${stake.apr}%</td>
                    <td>${stake.reward_acumulada.toFixed(4)}</td>
                    <td>${stake.reason}</td>
                    <td>${new Date(stake.moved_at).toLocaleString()}</td>
                </tr>
            `;

            historyTableBody.innerHTML += row;
        });

    } catch (e) {
        showToast("Error cargando historial", "err");
    }
}

/* ---------------------------------------------------------
   LIBERAR STAKE
--------------------------------------------------------- */
async function releaseStake(stake_id) {
    try {
        const res = await fetch(`${API}/dashboard/release/${stake_id}`, {
            method: "POST"
        });

        const data = await res.json();

        if (data.error) {
            showToast(data.error, "err");
        } else {
            showToast("Stake liberado", "ok");
            loadActiveStakes();
            loadHistory();
            loadWallet();
            loadRewards();
        }

    } catch (e) {
        showToast("Error liberando stake", "err");
    }
}

/* ---------------------------------------------------------
   CANCELAR STAKE
--------------------------------------------------------- */
async function cancelStake(stake_id) {
    try {
        const res = await fetch(`${API}/dashboard/cancel/${stake_id}`, {
            method: "POST"
        });

        const data = await res.json();

        if (data.error) {
            showToast(data.error, "err");
        } else {
            showToast("Stake cancelado", "ok");
            loadActiveStakes();
            loadHistory();
            loadWallet();
            loadRewards();
        }

    } catch (e) {
        showToast("Error cancelando stake", "err");
    }
}

/* ---------------------------------------------------------
   INICIALIZAR DASHBOARD
--------------------------------------------------------- */
async function initDashboard() {
    await loadWallet();
    await loadRewards();
    await loadActiveStakes();
    await loadHistory();

    // Actualizar cada 10 segundos
    setInterval(() => {
        loadRewards();
        loadActiveStakes();
    }, 10000);
}

initDashboard();
