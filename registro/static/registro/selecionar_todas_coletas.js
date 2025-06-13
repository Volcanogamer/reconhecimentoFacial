document.addEventListener('DOMContentLoaded', function () {
    const inlineGroup = document.querySelector('.inline-group');
    if (!inlineGroup) return;

    // Cria contêiner de botões
    const container = document.createElement('div');
    container.style.marginBottom = '15px';
    container.style.display = 'flex';
    container.style.gap = '10px';

    // Estilo comum para os botões
    const estiloBotao = `
        padding: 6px 12px;
        font-size: 14px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background 0.3s ease;
    `;

    // Botão Selecionar Todas
    const btnSelecionar = document.createElement('button');
    btnSelecionar.innerText = '✅ Selecionar todas';
    btnSelecionar.type = 'button';
    btnSelecionar.style.cssText = estiloBotao + 'background-color: #28a745; color: white;';
    btnSelecionar.onmouseenter = () => btnSelecionar.style.backgroundColor = '#218838';
    btnSelecionar.onmouseleave = () => btnSelecionar.style.backgroundColor = '#28a745';

    btnSelecionar.onclick = () => {
        const checkboxes = inlineGroup.querySelectorAll('input[type=checkbox][name$="-DELETE"]');
        checkboxes.forEach(cb => cb.checked = true);
    };

    // Botão Desmarcar Todas
    const btnDesmarcar = document.createElement('button');
    btnDesmarcar.innerText = '❌ Desmarcar todas';
    btnDesmarcar.type = 'button';
    btnDesmarcar.style.cssText = estiloBotao + 'background-color: #dc3545; color: white;';
    btnDesmarcar.onmouseenter = () => btnDesmarcar.style.backgroundColor = '#c82333';
    btnDesmarcar.onmouseleave = () => btnDesmarcar.style.backgroundColor = '#dc3545';

    btnDesmarcar.onclick = () => {
        const checkboxes = inlineGroup.querySelectorAll('input[type=checkbox][name$="-DELETE"]');
        checkboxes.forEach(cb => cb.checked = false);
    };

    // Adiciona os botões ao container
    container.appendChild(btnSelecionar);
    container.appendChild(btnDesmarcar);

    // Insere o container antes da lista de coletas
    inlineGroup.parentElement.insertBefore(container, inlineGroup);
});
