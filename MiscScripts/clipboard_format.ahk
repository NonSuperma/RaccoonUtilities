^+v::
{
    variable_1 := A_Clipboard
    A_Clipboard := ""
    Send "^x"
    if ClipWait(1)
    {
        variable_2 := A_Clipboard
        A_Clipboard := "[" variable_2 "](<" variable_1 ">)"
        Sleep 50
        Send "^v"
        Sleep 100
        A_Clipboard := variable_1
    }
}