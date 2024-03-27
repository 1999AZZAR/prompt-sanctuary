// toggle the side panel visibility
function toggleSidePanel() {
    var sidePanel = document.getElementById('sidePanel');
    sidePanel.style.transform = (sidePanel.style.transform === 'translateX(-100%)' || sidePanel.style.transform === '') ? 'translateX(0%)' : 'translateX(-100%)';
};