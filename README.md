# Monitor Service Desk

Aplicativo desktop desenvolvido em Python para monitorar automaticamente um número exibido na tela, utilizando captura de tela + OCR, e emitir um alerta sonoro quando o valor identificado muda.

O projeto nasceu de uma necessidade prática de monitoramento em uma rotina de Service Desk e foi estruturado como projeto de portfólio, com foco em automação, processamento de imagens, OCR, interface gráfica e execução em segundo plano.

## Problema

Acompanhar continuamente um indicador numérico exibido na tela pode consumir atenção e aumentar o risco de perceber uma alteração com atraso.

## Solução

O Monitor Service Desk permite:

- selecionar visualmente a região da tela que contém o número;
- trabalhar com múltiplos monitores;
- capturar a região selecionada automaticamente;
- reconhecer somente caracteres numéricos com Tesseract OCR;
- verificar o valor a cada 2 segundos;
- comparar o valor atual com o anterior;
- emitir alerta sonoro quando ocorre uma mudança;
- controlar um ciclo de tempo para atualização da página;
- funcionar independentemente do navegador utilizado para exibir a página monitorada.

## Fluxo

```text
Seleção da região
       ↓
Captura da tela
       ↓
Tesseract OCR
       ↓
Comparação do valor
       ↓
Valor mudou?
   ┌───┴───┐
  Não     Sim
           ↓
      Alerta sonoro
```

## Tecnologias

- Python 3
- Tkinter
- Pillow
- Tesseract OCR
- pytesseract
- screeninfo
- threading
- Windows winsound

## Estrutura

```text
monitor-servicedesk/
├── src/
│   └── monitor_servicedesk.py
├── screenshots/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
└── Monitor ServiceDesk.spec
```

## Instalação

Instale Python 3 no Windows.

Depois, na pasta do projeto:

```bash
python -m pip install -r requirements.txt
```

Instale também o Tesseract OCR. O código procura automaticamente:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
C:\Program Files (x86)\Tesseract-OCR\tesseract.exe
```

Se estiver em outro local, ajuste `TESSERACT_PATHS`.

## Execução

```bash
python src/monitor_servicedesk.py
```

## Utilização

1. Clique em **Selecionar número**.
2. Selecione a região que contém o número.
3. Use **Testar leitura** para validar o OCR.
4. Use **Testar som** para validar o alerta.
5. Configure o ciclo de atualização.
6. Inicie o monitoramento.
7. Quando o número mudar, o valor anterior e o atual são atualizados e um alerta sonoro é emitido.

## Atualização da página

O aplicativo não depende de Chrome, Edge ou outro navegador específico.

A atualização efetiva da página pode ser realizada por uma extensão de atualização automática configurada no navegador escolhido. O aplicativo mantém o controle visual do intervalo e registra o horário do ciclo.

## Conhecimentos demonstrados

- desenvolvimento de aplicação desktop;
- interface gráfica;
- captura de tela;
- OCR;
- processamento periódico em threads;
- comunicação com a interface usando `after`;
- comparação de estados;
- alertas sonoros;
- suporte a múltiplos monitores;
- tratamento de exceções;
- organização de dependências;
- preparação para distribuição.

## Limitações

- Projeto direcionado a Windows.
- A precisão depende da qualidade da imagem.
- O Tesseract precisa estar instalado.
- A região monitorada é selecionada pelo usuário.
- A atualização real da página é externa ao aplicativo.

## Melhorias futuras

- salvar a região selecionada;
- configurar intervalo de OCR;
- configurar intervalo de atualização pela interface;
- histórico de alterações;
- logs;
- diferentes tipos de alerta;
- instalador;
- inicialização com o Windows;
- pré-processamento avançado da imagem;
- testes automatizados;
- múltiplas regiões monitoradas.

## Autor

**Lucas Mattos**

Projeto desenvolvido para demonstrar aplicação prática de Python, automação e suporte a operações de Service Desk.
