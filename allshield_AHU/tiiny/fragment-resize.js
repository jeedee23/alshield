(() => {
  const fragment = new URL(window.location.href).pathname.split("/").pop();

  function reportHeight() {
    const height = Math.max(
      document.body.scrollHeight,
      document.body.offsetHeight
    );
    window.parent.postMessage({ type: "tiiny-fragment-height", fragment, height }, "*");
  }

  window.addEventListener("load", reportHeight);
  new ResizeObserver(reportHeight).observe(document.documentElement);
})();