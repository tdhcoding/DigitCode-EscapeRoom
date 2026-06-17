cmake_minimum_required(VERSION 3.16)
project(DigitCode_QT VERSION 0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(Qt6 REQUIRED COMPONENTS Quick)
qt_standard_project_setup(REQUIRES 6.10)

qt_add_executable(appDigitCode_QT
    main.cpp
    backend/gameboard.h
    backend/gameboard.cpp
)

qt_add_qml_module(appDigitCode_QT
    URI DigitCode_QT
    VERSION 1.0
    QML_FILES
        UI/Main.qml
        UI/LedDisplay.qml
        UI/LogicButton.qml
        UI/CounterBox.qml
        UI/EODot.qml
        UI/CmpArrow.qml
        UI/BottomBoard.qml
        UI/TopBoard.qml
        UI/DraftGrid.qml
)

set_target_properties(appDigitCode_QT PROPERTIES
    MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
    MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}
    MACOSX_BUNDLE TRUE
    WIN32_EXECUTABLE TRUE
)

target_link_libraries(appDigitCode_QT
    PRIVATE Qt6::Quick
)

install(TARGETS appDigitCode_QT
    BUNDLE DESTINATION .
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)