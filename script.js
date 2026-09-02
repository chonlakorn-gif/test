// script.js — preview รูปภาพที่ผู้ใช้เลือกก่อนกด submit ฟอร์ม

document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("image-input");
  const previewImg = document.getElementById("preview-img");
  const uploadIcon = document.getElementById("upload-icon");
  const uploadText = document.getElementById("upload-text");

  if (!input) return;

  input.addEventListener("change", () => {
    const file = input.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewImg.classList.remove("hidden");
      uploadIcon.classList.add("hidden");
      uploadText.textContent = file.name;
    };
    reader.readAsDataURL(file);
  });
});
