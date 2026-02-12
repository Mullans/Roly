from rollie import main


def test_main_prints_expected_output(capsys):
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "Hello from rollie!"
