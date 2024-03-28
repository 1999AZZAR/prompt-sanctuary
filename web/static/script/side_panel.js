// toggle the side panel visibility
function toggleSidePanel() {
    var sidePanel = document.getElementById('sidePanel');
    var isPanelVisible = sidePanel.style.transform === 'translateX(0%)';

    sidePanel.style.transform = isPanelVisible ? 'translateX(-100%)' : 'translateX(0%)';
}