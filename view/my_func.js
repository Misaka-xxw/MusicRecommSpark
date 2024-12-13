function correct_dialog(msg) {
    this.$message({
        showClose: true,
        message: msg,
        type: 'success'
    });
}
function error_dialog(msg) {
    this.$message({
        showClose: true,
        message: msg,
        type: 'error'
    });
}