

// 随机选择背景图片
document.body.style.backgroundImage = `url(./img/bg${Math.floor(Math.random() * 7)}.jpg)`;
// body后插入info-box id=description
let descriptionDiv = document.createElement("div");
descriptionDiv.className = 'info-box'
descriptionDiv.id = 'author-description'

// 添加一副头像且垂直居中
let avatar1 = document.createElement("img");
avatar1.src = 'https://q.qlogo.cn/g?b=qq&nk=2751454815&s=640'
avatar1.style.height = '50px';
// avatar.style.borderRadius = '50%';

let avatar2 = document.createElement("img");
avatar2.src = 'https://q.qlogo.cn/g?b=qq&nk=3657522512&s=640'
avatar2.style.height = '50px';

let text1 = document.createElement("div");
text1.id = 'author-text';
text1.innerText = '该页样式由：';

let text2 = document.createElement("div");
text2.id = 'author-text';
text2.innerText = ' 神羽SnowyKami 设计；';

let text3 = document.createElement("div");
text3.id = 'author-text';
text3.innerText = ' 金羿Eilles 方角美化';

descriptionDiv.appendChild(text1);
descriptionDiv.appendChild(avatar1);
descriptionDiv.appendChild(text2);
descriptionDiv.appendChild(avatar2);
descriptionDiv.appendChild(text3);

document.body.appendChild(descriptionDiv);
