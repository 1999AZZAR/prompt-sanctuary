// Toggle Sidebar
function toggleSidePanel() {
    const sidePanel = document.getElementById('sidePanel');
    sidePanel.classList.toggle('-translate-x-full');
}

// Close Sidebar When Clicking Outside
document.addEventListener('click', (event) => {
    const sidePanel = document.getElementById('sidePanel');
    const heroSection = document.querySelector('.hero');
    const logo = document.querySelector('.side-panel .p-6');

    if (!sidePanel.contains(event.target) && !heroSection.contains(event.target) && !logo.contains(event.target)) {
        sidePanel.classList.add('-translate-x-full');
    }
});
